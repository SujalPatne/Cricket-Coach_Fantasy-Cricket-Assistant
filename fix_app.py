# Helper function to process quick action button clicks
def handle_quick_action(query):
    """Process a quick action button click with proper message ordering"""
    # Import time module at the function level to avoid scoping issues
    import time
    
    # Add user message to chat history
    st.session_state.past.append(query)

    # Log access
    log_access(
        user_id=st.session_state.get('db_user_id', st.session_state.get('user_id', 'anonymous')),
        endpoint="quick_action",
        method="POST"
    )

    # Use the status container to show detailed status messages
    with status_container:
        # Create a placeholder for the status message
        status_placeholder = st.empty()

        # Show initial "thinking" message
        status_placeholder.info("⌛ The assistant is thinking...")

        try:
            # Process query with AI manager
            ai_manager = st.session_state['ai_manager']

            # Update status based on the quick action type
            if "batsmen" in query.lower():
                status_placeholder.info("⌛ Finding the best batsmen for today's matches...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Analyzing batsmen form and matchups...")
            elif "bowlers" in query.lower():
                status_placeholder.info("⌛ Analyzing top bowlers for fantasy cricket...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Evaluating bowling conditions and recent performances...")
            elif "differential" in query.lower():
                status_placeholder.info("⌛ Finding differential picks for today's matches...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Analyzing player ownership and form...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Identifying under-the-radar players...")
            elif "captain" in query.lower():
                status_placeholder.info("⌛ Identifying best captain and vice-captain options...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Analyzing player form and matchups...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Calculating multiplier value...")
            elif "fantasy" in query.lower() or "tips" in query.lower():
                status_placeholder.info("⌛ Generating fantasy cricket advice...")
                time.sleep(0.5)
                status_placeholder.info("⌛ Compiling team selection strategies...")
            elif "stats" in query.lower():
                status_placeholder.info("⌛ Preparing player statistics options...")
            else:
                status_placeholder.info("⌛ Processing your request...")

            # Process the query
            result = ai_manager.process_query(query)

            # Update status to show we're formatting the response
            status_placeholder.info("⌛ Formatting response...")

            # Check if result contains a response
            if result and "response" in result:
                output = result["response"]
                model_used = result.get("model_used", "unknown")
            else:
                # Fallback response if something went wrong
                output = "I'm sorry, I couldn't generate a response. Please try again."
                model_used = "fallback"

            # Log chat interaction
            log_chat(
                user_id=st.session_state.get('db_user_id', st.session_state.get('user_id', 'anonymous')),
                query=query,
                response=output[:100] + "..." if len(output) > 100 else output,
                model_used=model_used
            )

            # Clear the status message when done
            status_placeholder.empty()

        except Exception as e:
            output = f"I'm having trouble processing your request. Please try again. Error: {str(e)}"
            log_error(e, context={"quick_action": query})

            # Show error in status
            status_placeholder.error("❌ Error processing your request")
            # Clear after 3 seconds
            time.sleep(3)
            status_placeholder.empty()

    # Save to database if user is authenticated
    try:
        if st.session_state.get('authenticated', False):
            db = st.session_state['db_manager']
            user_id = st.session_state.get('db_user_id')

            db.save_chat(
                user_id=user_id,
                user_message=query,
                assistant_response=output,
                ai_model_used=model_used if 'model_used' in locals() else "unknown"
            )
    except Exception as e:
        log_error(e, context={"action": "save_quick_action"})

    # Add assistant response to chat history
    st.session_state.generated.append(output)

    # Force a rerun to update the UI
    st.rerun()
