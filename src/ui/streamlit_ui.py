import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.colored_header import colored_header
from streamlit_extras.card import card
from typing import Tuple
import logging
from ..models.data_models import UserPreferences
from ..services.course_recommender import CourseRecommender
from .styles import STREAMLIT_STYLE
from ..utils.enums import LearningFormat, ExperienceLevel, CareerGoal

class StreamlitUI:
    def __init__(self):
        self.initialize_session_state()
        
    def initialize_session_state(self):
        if 'initialized' not in st.session_state:
            st.session_state.update({
                'initialized': True,
                'step': 0,
                'user_responses': {},
                'ready_for_recommendations': False,
                'recommendations_generated': False,
                'current_recommendations': None,
                'current_results': None,
                'error_message': None,
                'theme_color': '#3b71ca',
                'api_key_valid': False,
                'api_key': None
            })

    def validate_api_key(self, api_key: str) -> bool:
        """Validate if the API key is in the correct format."""
        return api_key.startswith('gsk_') and len(api_key) > 20

    def render_questionnaire(self) -> bool:
        questions = [
            ("Please enter your name:", "user_name", None),
            ("What subject or skill would you like to learn?", "subject", None),
            ("How many hours per week can you dedicate to learning?", "availability", 
             ["1-2 hours", "3-5 hours", "6-10 hours", "More than 10 hours"]),
            ("What is your maximum budget for this course?", "budget", None),
            ("What is your preferred learning format?", "format", [f.value for f in LearningFormat]),
            ("What is your current experience level?", "experience", [e.value for e in ExperienceLevel]),
            ("What is your primary goal?", "goal", [g.value for g in CareerGoal])
        ]

        if st.session_state.step >= len(questions):
            return self.handle_questionnaire_completion()

        # Create a container for the questionnaire
        with st.container():
            colored_header(
                label=f"Step {st.session_state.step + 1} of {len(questions)}",
                description="Tell us about your learning preferences",
                color_name="blue-70"
            )

            progress = min(st.session_state.step / (len(questions) - 1), 1.0)
            st.progress(progress)

            current_question = questions[st.session_state.step]
            return self.handle_current_question(current_question)

    def handle_current_question(self, question_data: Tuple) -> bool:
        question, key, options = question_data
        
        with st.form(key=f"question_form_{key}"):
            st.write(f"### {question}")
            
            if options:
                user_input = st.selectbox(
                    "Choose an option:",
                    options,
                    key=f"input_{key}",
                    help=f"Select your preferred {key}"
                )
            elif key == "budget":
                budget_ranges = [
                    {"label": "Free Courses Only", "value": 0},
                    {"label": "< $50", "value": 50},
                    {"label": "< $100", "value": 100},
                    {"label": "< $200", "value": 200},
                    {"label": "< $500", "value": 500},
                    {"label": "< $1000", "value": 1000},
                    {"label": "Over $1000", "value": 1500}
                ]
                
                selected_range = st.radio(
                    "Select your budget range:",
                    options=[r["label"] for r in budget_ranges],
                    key="budget_range",
                    horizontal=True,
                    help="Choose your preferred budget range for the course"
                )
                
                # Get the corresponding value for the selected range
                user_input = next(
                    (r["value"] for r in budget_ranges if r["label"] == selected_range),
                    100
                )
            else:
                user_input = st.text_input(
                    "Your answer:",
                    key=f"input_{key}",
                    placeholder=f"Enter your {key.replace('_', ' ')}",
                    help=f"Enter your {key.replace('_', ' ')}"
                )

            submit_button = st.form_submit_button(
                "Next" if st.session_state.step < 6 else "Get Recommendations"
            )

            if submit_button and (user_input or user_input == 0):
                self.save_user_input(key, user_input)
                st.session_state.step += 1
                st.rerun()

        return False

    def save_user_input(self, key: str, user_input: str):
        st.session_state.user_responses[key] = user_input

    def handle_questionnaire_completion(self) -> bool:
        """Handle the completion of the questionnaire and prepare for recommendations."""
        try:
            if not all(key in st.session_state.user_responses for key in ['user_name', 'subject', 'availability', 'budget', 'format', 'experience', 'goal']):
                st.error("Please complete all questions before proceeding.")
                self.reset_session()
                return False

            preferences = UserPreferences(
                name=st.session_state.user_responses['user_name'],
                subject=st.session_state.user_responses['subject'],
                availability=st.session_state.user_responses['availability'],
                budget=int(st.session_state.user_responses['budget']),
                format=st.session_state.user_responses['format'],
                experience=st.session_state.user_responses['experience'],
                goal=st.session_state.user_responses['goal']
            )
            
            with st.spinner('Generating recommendations...'):
                recommendations, additional_results = self.recommender.generate_recommendations(preferences)
                
                if isinstance(recommendations, str) and "Error" in recommendations:
                    st.error(recommendations)
                    return False
                
                st.session_state.current_recommendations = recommendations
                st.session_state.current_results = additional_results
                st.session_state.ready_for_recommendations = True
                st.session_state.recommendations_generated = True
                st.session_state.user_name = preferences.name
                
                return True
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logging.error(f"Error in handle_questionnaire_completion: {str(e)}")
            return False

    def reset_session(self):
        """Reset the session state to initial values."""
        api_key = st.session_state.api_key  # Preserve API key
        api_key_valid = st.session_state.api_key_valid  # Preserve API key validation status
        st.session_state.clear()
        st.session_state.update({
            'step': 0,
            'user_responses': {},
            'ready_for_recommendations': False,
            'recommendations_generated': False,
            'current_recommendations': None,
            'current_results': None,
            'error_message': None,
            'api_key': api_key,
            'api_key_valid': api_key_valid
        })

    def display_recommendations(self):
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
            if st.button("Try Again", use_container_width=True):
                self.reset_session()
                st.rerun()
            return

        if not st.session_state.current_recommendations:
            st.warning("No recommendations available. Please start a new search.")
            if st.button("Start New Search", use_container_width=True):
                self.reset_session()
                st.rerun()
            return

        colored_header(
            label=f"Personalized Course Recommendations for {st.session_state.user_name}",
            description="Based on your preferences, we recommend the following courses:",
            color_name="blue-70"
        )

        # Display recommendations in a modern card layout
        col1, col2 = st.columns([7, 3])
        
        with col1:
            with st.container():
                st.markdown(
                    f"""<div class="recommendation-card">
                        {st.session_state.current_recommendations}
                    </div>""", 
                    unsafe_allow_html=True
                )

        with col2:
            with st.container():
                st.write("### Quick Summary")
                st.info(f"""
                **Selected Preferences:**
                - Subject: {st.session_state.user_responses.get('subject')}
                - Format: {st.session_state.user_responses.get('format')}
                - Level: {st.session_state.user_responses.get('experience')}
                """)

                if st.button("Start New Search", key="new_search", use_container_width=True):
                    self.reset_session()
                    st.rerun()

            # Additional resources in a collapsible section
            with st.expander("📚 Additional Learning Resources", expanded=False):
                if st.session_state.current_results:
                    for result in st.session_state.current_results[:3]:
                        card(
                            title=result['title'],
                            text=result['body'],
                            url=result['href']
                        )
                else:
                    st.info("No additional resources found.")

        st.markdown("---")
        
        # Footer with helpful information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("🔍 Verify course details on respective platforms")
        with col2:
            st.info("💡 Consider prerequisites before enrolling")
        with col3:
            st.info("📅 Check course start dates and deadlines")

    def generate_recommendations(self):
        """Generate course recommendations based on user preferences."""
        try:
            preferences = UserPreferences(
                name=st.session_state.user_responses.get('user_name', ''),
                subject=st.session_state.user_responses.get('subject', ''),
                availability=st.session_state.user_responses.get('availability', ''),
                budget=int(st.session_state.user_responses.get('budget', 0)),
                format=st.session_state.user_responses.get('format', ''),
                experience=st.session_state.user_responses.get('experience', ''),
                goal=st.session_state.user_responses.get('goal', '')
            )

            with st.spinner('Generating personalized course recommendations...'):
                recommendations, additional_results = self.recommender.generate_recommendations(preferences)
                
                if recommendations:
                    st.session_state.current_recommendations = recommendations
                    st.session_state.current_results = additional_results
                    st.session_state.recommendations_generated = True
                    st.session_state.user_name = preferences.name
                else:
                    st.session_state.error_message = "Unable to generate recommendations. Please try again."
                
                st.rerun()

        except Exception as e:
            st.session_state.error_message = f"Error generating recommendations: {str(e)}"
            st.rerun()

    def run(self):
        with st.sidebar:
            st.image("src/ui/assets/logo.png")
            st.markdown("---")
            
            # Add API key input section with updated instructions
            st.markdown("### Groq API Key Setup")
            st.markdown("""
            To use the course recommender, you need a Groq API key.
            If you don't have one, you can get it from:
            [Groq Console](https://console.groq.com/keys) 🔑
            """)
            
            api_key = st.text_input(
                "Enter your Groq API Key:",
                type="password",
                help="Enter your Groq API key to use the course recommender",
                key="api_key_input"
            )
            
            if api_key:
                if self.validate_api_key(api_key):
                    st.session_state.api_key = api_key
                    st.session_state.api_key_valid = True
                    self.recommender = CourseRecommender(api_key=api_key)
                else:
                    st.error("Invalid Groq API key format. It should start with 'gsk_'")
                    st.session_state.api_key_valid = False
            
            st.markdown("---")
            st.markdown("""
            ### How it works
            1. Share your preferences
            2. Get personalized recommendations
            3. Explore course options
            """)
            st.markdown("---")
            if st.button("Reset Application", use_container_width=True):
                self.reset_session()
                st.rerun()

        # Main content area with improved API key validation message
        if not st.session_state.api_key_valid:
            st.error("⚠️ Please enter your Groq API key in the sidebar to use the course recommender.")
            st.info("Don't have an API key? Get one for free from [Groq Console](https://console.groq.com/keys)")
            return

        # Main content area with error handling
        try:
            if not st.session_state.ready_for_recommendations:
                if self.render_questionnaire():
                    st.session_state.ready_for_recommendations = True
                    st.rerun()
            elif st.session_state.recommendations_generated:
                self.display_recommendations()
            else:
                self.generate_recommendations()
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            logging.error(f"Error in main UI flow: {str(e)}")
            if st.button("Start Over"):
                self.reset_session()
                st.rerun()

