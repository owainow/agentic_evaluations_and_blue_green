#!/usr/bin/env python3
"""
Agent Creation Script for Azure AI Foundry with Azure Functions Integration
Creates an AI agent with function tools that call Azure Functions via the agent function calling mechanism
"""

import os
import sys
import json
import requests
import time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def create_function_tool_definition():
    """
    Create function tool definitions that match the Azure Functions API
    These definitions tell the agent about the available functions and their parameters
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state/country, e.g. 'Seattle, WA' or 'London, UK'"
                        },
                        "unit": {
                            "type": "string",
                            "description": "Temperature unit - 'celsius' or 'fahrenheit'",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_news_articles",
                "description": "Get news articles related to a specific topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic or keyword to search for news articles"
                        },
                        "max_articles": {
                            "type": "integer",
                            "description": "Maximum number of articles to return",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        }
                    },
                    "required": ["topic"]
                }
            }
        }
    ]


def call_azure_function(function_name: str, parameters: dict, function_app_url: str) -> str:
    """
    Call an Azure Function with the given parameters
    This function is called by the agent when it needs to execute a tool
    
    Args:
        function_name: Name of the function to call (get_weather or get_news_articles)
        parameters: Dictionary of parameters to pass to the function
        function_app_url: Base URL of the Function App
    
    Returns:
        JSON string response from the function
    """
    try:
        url = f"{function_app_url}/api/{function_name}"
        
        # Make the HTTP request to the Azure Function
        response = requests.post(
            url,
            json=parameters,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.text
        else:
            error_result = {
                "error": f"Function call failed with status {response.status_code}",
                "details": response.text,
                "function": function_name,
                "parameters": parameters
            }
            return json.dumps(error_result)
            
    except Exception as e:
        error_result = {
            "error": f"Failed to call Azure Function: {str(e)}",
            "function": function_name,
            "parameters": parameters
        }
        return json.dumps(error_result)


def handle_function_calls(run, project_client, thread_id, function_app_url):
    """
    Handle function calls when the agent requires action
    This is the core function calling handler that executes Azure Functions
    
    Args:
        run: The current run object
        project_client: AIProjectClient instance
        thread_id: Thread ID
        function_app_url: Azure Function App URL
    
    Returns:
        Updated run object after submitting tool outputs
    """
    if run.status == "requires_action":
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []
        
        print(f"Agent is requesting {len(tool_calls)} function call(s)...")
        
        for tool_call in tool_calls:
            print(f"  Executing function: {tool_call.function.name}")
            
            # Parse function arguments
            try:
                function_args = json.loads(tool_call.function.arguments)
                print(f"    Arguments: {function_args}")
            except json.JSONDecodeError:
                function_args = {}
                print(f"    Warning: Could not parse arguments: {tool_call.function.arguments}")
            
            # Call the appropriate Azure Function
            if tool_call.function.name in ["get_weather", "get_news_articles"]:
                output = call_azure_function(
                    function_name=tool_call.function.name,
                    parameters=function_args,
                    function_app_url=function_app_url
                )
                print(f"    Function returned: {output[:100]}...")
                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            else:
                # Unknown function
                error_output = json.dumps({
                    "error": f"Unknown function: {tool_call.function.name}"
                })
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": error_output
                })
        
        # Submit tool outputs back to the agent
        print("Submitting function results back to agent...")
        run = project_client.agents.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
        print(f"Tool outputs submitted. Run status: {run.status}")
    
    return run


def create_agent(
    project_endpoint: str,
    model_deployment_name: str,
    agent_name: str,
    agent_instructions: str,
    function_app_url: str = None,
    agent_description: str = None
):
    """
    Create an AI agent in Azure AI Foundry with Azure Functions integration
    
    Args:
        project_endpoint: Azure AI Foundry project endpoint
        model_deployment_name: Name of the deployed model to use
        agent_name: Name for the agent
        agent_instructions: Instructions for the agent behavior
        function_app_url: URL of the Azure Function App (if None, will use environment variable)
        agent_description: Optional description of the agent
    
    Returns:
        dict: Agent metadata including ID and details
    """
    try:
        # Get Function App URL from parameter or environment
        if not function_app_url:
            function_app_url = os.getenv('FUNCTION_APP_URL')
            if not function_app_url:
                raise ValueError("Function App URL must be provided either as parameter or FUNCTION_APP_URL environment variable")
        
        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()
        
        # Create project client
        print(f"Connecting to project: {project_endpoint}")
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=credential
        )
        
        # Create function tool definitions for Azure Functions
        print("Setting up Azure Function tool definitions...")
        function_tools = create_function_tool_definition()
        
        # Enhanced instructions that work with function calling
        enhanced_instructions = f"""{agent_instructions}

CRITICAL RULES - You MUST follow these without exception:

1. FUNCTION CALLING:
   - You have access to two functions: get_weather and get_news_articles
   - ALWAYS use the appropriate function when users ask about weather or news
   - Wait for function results before responding to the user

2. WEATHER QUERIES:
   - Use the get_weather function for any weather-related questions
   - Pass the location parameter from the user's query
   - Include unit preference if specified by the user
   - Present the weather information in a user-friendly format

3. NEWS QUERIES:
   - Use the get_news_articles function for any news-related questions
   - Pass the topic parameter from the user's query
   - Include max_articles if the user specifies how many they want
   - Present the news articles in a clear, readable format

4. RESPONSE FORMAT:
   - Always wait for function execution to complete
   - Present function results in a user-friendly way
   - Don't return raw JSON unless specifically requested

5. ERROR HANDLING:
   - If a function call fails, inform the user that the service is temporarily unavailable
   - Do NOT make up data if the function returns an error
   - Be helpful and suggest alternatives when possible

6. OUT OF SCOPE:
   - For non-weather and non-news queries, politely explain your capabilities
   - Stay focused on weather and news information only
"""
        
        # Create the agent with function tools
        print(f"Creating agent '{agent_name}' with model '{model_deployment_name}' and Azure Functions...")
        print(f"Function App URL: {function_app_url}")
        
        agent = project_client.agents.create_agent(
            model=model_deployment_name,
            name=agent_name,
            instructions=enhanced_instructions,
            tools=function_tools,
            description=agent_description or f"Weather and news agent using {model_deployment_name} with Azure Functions"
        )
        
        print(f"✓ Agent created successfully!")
        print(f"  Agent ID: {agent.id}")
        print(f"  Agent Name: {agent.name}")
        print(f"  Model: {agent.model}")
        print(f"  Tools: {len(function_tools)} Azure Function(s) enabled")
        
        # Return agent details
        return {
            "id": agent.id,
            "name": agent.name,
            "model": agent.model,
            "instructions": agent.instructions,
            "description": agent.description,
            "function_app_url": function_app_url,
            "created_at": str(agent.created_at) if hasattr(agent, 'created_at') else None,
            "tools_count": len(function_tools)
        }
        
    except Exception as e:
        print(f"✗ Error creating agent: {str(e)}", file=sys.stderr)
        raise


def test_agent_with_azure_functions(project_client, agent_id, function_app_url, test_query="What's the weather in Seattle?"):
    """
    Test the agent with a query to verify Azure Functions integration
    
    Args:
        project_client: AIProjectClient instance
        agent_id: ID of the agent to test
        function_app_url: Azure Function App URL
        test_query: Query to test
    
    Returns:
        dict: Test results including response and success status
    """
    print(f"\n--- Testing Agent with Azure Functions ---")
    print(f"Query: {test_query}")
    
    try:
        # Create a thread for testing
        thread = project_client.agents.threads.create()
        print(f"Created test thread: {thread.id}")
        
        # Send the test message
        message = project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=test_query
        )
        print(f"Sent message: {message.id}")
        
        # Run the agent
        run = project_client.agents.runs.create(
            thread_id=thread.id,
            agent_id=agent_id
        )
        print(f"Started run: {run.id}")
        
        # Wait for completion with timeout and handle function calls
        max_wait_time = 120  # seconds
        wait_time = 0
        poll_interval = 2
        
        while run.status in ["queued", "in_progress", "requires_action"] and wait_time < max_wait_time:
            time.sleep(poll_interval)
            wait_time += poll_interval
            run = project_client.agents.runs.get(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"Run status: {run.status} (waited {wait_time}s)")
            
            # Handle function calls when agent requires action
            if run.status == "requires_action":
                run = handle_function_calls(run, project_client, thread.id, function_app_url)
        
        print(f"Final run status: {run.status} after {wait_time}s")
        
        # Handle different completion states
        if run.status == "completed":
            # Get the response
            try:
                messages = project_client.agents.messages.list(
                    thread_id=thread.id,
                    order="asc"
                )
            except TypeError:
                # Fallback without order parameter if not supported
                messages = project_client.agents.messages.list(thread_id=thread.id)
            
            # Find the assistant's response
            response_content = None
            message_list = list(messages)  # Convert ItemPaged to list
            
            print(f"Found {len(message_list)} messages in thread")
            for i, msg in enumerate(message_list):
                print(f"  Message {i}: role={msg.role}, content_length={len(msg.content) if msg.content else 0}")
                if msg.role == "assistant" and msg.content:
                    response_content = msg.content[0].text.value if msg.content else None
                    break
            
            if response_content:
                print(f"✓ Agent responded successfully")
                print(f"Response: {response_content[:200]}..." if len(response_content or "") > 200 else f"Response: {response_content}")
                
                return {
                    "success": True,
                    "response": response_content,
                    "run_status": run.status,
                    "execution_time": wait_time
                }
            else:
                print(f"✗ No assistant response found in messages")
                return {
                    "success": False,
                    "error": "No assistant response found in thread messages",
                    "run_status": run.status,
                    "execution_time": wait_time
                }
        elif run.status == "failed":
            error_details = getattr(run, 'last_error', None)
            error_message = f"Run failed: {error_details}" if error_details else "Run failed with unknown error"
            print(f"✗ {error_message}")
            return {
                "success": False,
                "error": error_message,
                "run_status": run.status,
                "execution_time": wait_time
            }
        elif run.status in ["queued", "in_progress", "requires_action"]:
            print(f"✗ Run timed out after {max_wait_time}s with status: {run.status}")
            return {
                "success": False,
                "error": f"Run timed out after {max_wait_time}s with status: {run.status}",
                "run_status": run.status,
                "execution_time": wait_time
            }
        else:
            print(f"✗ Agent completed with unexpected status: {run.status}")
            return {
                "success": False,
                "error": f"Agent run completed with unexpected status: {run.status}",
                "run_status": run.status,
                "execution_time": wait_time
            }
            
    except Exception as e:
        print(f"✗ Error testing agent: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main function to create the agent"""
    # Get environment variables
    project_endpoint = os.getenv('PROJECT_ENDPOINT') or os.getenv('AZURE_AI_PROJECT_ENDPOINT')
    model_deployment_name = os.getenv('MODEL_DEPLOYMENT_NAME', 'gpt-4o-deployment')
    function_app_url = os.getenv('FUNCTION_APP_URL')  # Required for Azure Functions
    agent_name = os.getenv('AGENT_NAME', 'WeatherNewsAgent-AzureFunctions')
    agent_instructions = os.getenv('AGENT_INSTRUCTIONS', """You are a specialized weather and news information agent. 
Your primary function is to provide accurate weather information and current news articles using Azure Functions.
You should be helpful and present information in a user-friendly way.""")
    
    if not project_endpoint:
        print("Error: PROJECT_ENDPOINT environment variable is required")
        print("Set it to your Azure AI Foundry project endpoint")
        sys.exit(1)
    
    if not function_app_url:
        print("Error: FUNCTION_APP_URL environment variable is required")
        print("Set it to your Azure Function App URL, e.g.: https://my-function-app.azurewebsites.net")
        sys.exit(1)
    
    try:
        print("=== Azure AI Foundry Agent Creation with Azure Functions ===")
        print(f"Project: {project_endpoint}")
        print(f"Model: {model_deployment_name}")
        print(f"Function App: {function_app_url}")
        print()
        
        # Create the agent
        agent_details = create_agent(
            project_endpoint=project_endpoint,
            model_deployment_name=model_deployment_name,
            agent_name=agent_name,
            agent_instructions=agent_instructions,
            function_app_url=function_app_url
        )
        
        # Test the agent
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=credential
        )
        
        test_result = test_agent_with_azure_functions(
            project_client=project_client,
            agent_id=agent_details["id"],
            function_app_url=function_app_url,
            test_query="What's the weather in London?"
        )
        
        # Save agent details to file
        output_file = "agent_details_azure_functions.json"
        with open(output_file, 'w') as f:
            json.dump({
                **agent_details,
                "test_result": test_result
            }, f, indent=2)
        
        print(f"\n✓ Agent details saved to: {output_file}")
        print(f"✓ Agent ID: {agent_details['id']}")
        
        # Output for GitHub Actions
        github_output = os.getenv('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"agentId={agent_details['id']}\n")
                f.write(f"agentName={agent_details['name']}\n")
                f.write(f"functionAppUrl={function_app_url}\n")
        
        if test_result.get("success"):
            print("✓ Agent test completed successfully")
        else:
            print("✗ Agent test failed")
            
    except Exception as e:
        print(f"✗ Failed to create agent: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()