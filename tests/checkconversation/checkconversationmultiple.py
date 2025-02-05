import requests
import time
from datetime import datetime

def check_conversation_status():
    url = "http://localhost:10502/conversation"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    body = {
        "swarm": "qr-swarm",
        "user": "test",
        "request": "Define the quality rules and tests for web_sales table"
    }

    try:
        post_response = requests.post(url, headers=headers, json=body)
        post_response.raise_for_status()
        post_res = post_response.json()

        user_id = post_res["header"]["user_id"]
        conversation_id = post_res["header"]["conversation_id"]

        print(f"user_id: {user_id}")
        print(f"conversation_id: {conversation_id}")

        # assert isinstance(user_id, str), "user_id is not a String"
        # assert isinstance(conversation_id, str), "conversation_id is not a String"
        # assert user_id == "test", "user_id doesn't match 'test'"
        # assert "test_" in conversation_id, "conversation_id doesn't contain 'test_'"
        # print("All POST asserts validated successfully.")

        get_url = f"{url}/{user_id}/{conversation_id}"
        max_wait_time = 9*60
        pending = False
        start_time = time.time()

        while True:
            get_response = requests.get(get_url, headers=headers)
            get_response.raise_for_status()
            get_res = get_response.json()

            pending = get_res["messages"][-1]["pending_user_reply"]
            if pending is True:
                result = "The conversation is over."
                print(result)
                print("\n")
                print(get_res)
                print("\n")
                break
            else:
                elapsed_time = time.time() - start_time
                if elapsed_time >= max_wait_time:
                    result = "The waiting time has exceeded 9 minutes. Ending the process."
                    print(result)
                    break
                else:
                    # print("The conversation is not over yet. Waiting 30 seconds...")
                    time.sleep(30)
        # assert pending is True, "pending_user_reply is not True. The conversation is not over yet."
        # print("Assert pending_user_reply validated successfully.")
        return result, get_res, start_time, time.time()

    except requests.exceptions.RequestException as error:
        print(f"Error during the request: {error}")

    except AssertionError as assert_error:
        print(f"Validation error: {assert_error}")


def run_multiple_tests(num_tests):
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"results/results_{current_datetime}.csv"
    with open(file_name, "w") as file:
        file.write("Test Number~ Start Time~ End Time~ Duration (seconds)~ Result~ Conversation\n")
        
        for i in range(1, num_tests + 1):
            print(f"Running test {i}/{num_tests}...")
            result, get_res, start_time, end_time = check_conversation_status()
            
            duration = end_time - start_time
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes:02d}:{seconds:02d}"
            start_time_str = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
            end_time_str = datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S")
            
            file.write(f"{i}~ {start_time_str}~ {end_time_str}~ {duration_str}~ {result}~ {get_res}\n\n")
            print(f"Test {i} completed and saved.")

run_multiple_tests(10)