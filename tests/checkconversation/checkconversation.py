import requests
import time

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

    assert isinstance(user_id, str), "user_id is not a String"
    assert isinstance(conversation_id, str), "conversation_id is not a String"
    assert user_id == "test", "user_id doesn't match 'test'"
    assert "test_" in conversation_id, "conversation_id doesn't contain 'test_'"
    print("All POST asserts validated successfully.")

    get_url = f"{url}/{user_id}/{conversation_id}"
    max_wait_time = 540
    pending = False
    start_time = time.time()

    while True:
        get_response = requests.get(get_url, headers=headers)
        get_response.raise_for_status()
        get_res = get_response.json()

        pending = get_res["messages"][-1]["pending_user_reply"]
        if pending is True:
            print("The conversation is over.")
            print("\n")
            print(get_res)
            print("\n")
            break
        else:
            elapsed_time = time.time() - start_time
            if elapsed_time >= max_wait_time:
                print("The waiting time has exceeded 9 minutes. Ending the process.")
                break
            else:
                print("The conversation is not over yet. Waiting 30 seconds...")
                time.sleep(30)
    assert pending is True, "pending_user_reply is not True. The conversation is not over yet."
    print("Assert pending_user_reply validated successfully.")

except requests.exceptions.RequestException as error:
    print(f"Error during the request: {error}")

except AssertionError as assert_error:
    print(f"Validation error: {assert_error}")