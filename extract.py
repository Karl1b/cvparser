import json
import os
import requests
from pdfminer.high_level import extract_text

def extract_text_from_pdfs(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(
                output_folder, f"{os.path.splitext(filename)[0]}.txt"
            )
            text = extract_text(input_path)

            with open(output_path, "w", encoding="utf-8") as text_file:
                text_file.write(text)

            print(f"Extracted text from {filename} to {output_path}")

def query_ollama(text):
    url = "http://localhost:11434/api/generate"
    payload = {"model": "llama3", "prompt": text}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers, stream=True)

    if response.status_code == 200:
        # Read the stream of JSON objects
        full_response = ""
        for line in response.iter_lines():
            if line:
                json_response = line.decode("utf-8")
                try:
                    response_data = json.loads(json_response)
                    full_response += response_data.get("response", "")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON response: {e}")
                    print(f"Response received: {json_response}")
                    return "Error processing response"
        return full_response
    else:
        return f"Error: {response.status_code}"

prompt = """
This is a CV skill extractor. You will receive a List of CVs. If the person has another skill which is not in the list,
add it to the list. Guess if the person has this skill and rate the skills based on the CV on a scale from 0-9.
Where 0 is that the candidate does not have this skill, and 9 is that the candidate is an expert.
Please give back a List of skills.
ANSWER WITH ALL SKILLS. DO NOT WRITE ANYTHING ELSE.
EXAMPLE RESPONSE:
[{"skill": "JavaScript", "level":5 },{"skill":"English","level":0},{"skill":"C++","level":4}]
"""
skills = """
THIS IS YOUR CURRENT SKILL LIST IF YOU FIND A SKILL THAT IS LIKE ONE OF THOSE IN THE LIST, SPELL IT EXACTLY THE SAME WAY, USE ALL OF THE SKILLS, SIMPLY SELECT level 0 for it if the candidate does not have it.:
"""
skilllist = "JavaScript,English,C++,Python,Django,Java,German"

if __name__ == "__main__":
    input_folder = "pdf"
    output_folder = "text"
    skillfolder = "skilllist"
    extract_text_from_pdfs(input_folder, output_folder)

    for filename in os.listdir(output_folder):
        if filename.endswith(".txt"):
            with open(os.path.join(output_folder, filename), 'r', encoding='utf-8') as file:
                file_content = file.read()
            queryprompt = prompt + skills + skilllist + "\nFILE CONTENT:\n" + file_content
            print(f"Querying Ollama with the content of {filename}")

            ollama_response = query_ollama(queryprompt)
            print(ollama_response)
            # Parse the response JSON array and update the skill list
            try:
                skills_response = json.loads(ollama_response)
                new_skills = [skill["skill"] for skill in skills_response]
                skilllist += "," + ",".join(new_skills)
                print("Updated Skill List:", skilllist)
                
                # Save the Ollama response to a text file named like the filename with _result
                response_filename = os.path.join(skillfolder, f"{os.path.splitext(filename)[0]}_result.txt")
                with open(response_filename, 'w', encoding='utf-8') as response_file:
                    response_file.write(ollama_response)
                    
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                print("Response received:", ollama_response)

    # Save the final skill list to a text file
    final_skilllist_path = os.path.join(skillfolder, "final_skilllist.txt")
    with open(final_skilllist_path, 'w', encoding='utf-8') as final_skilllist_file:
        final_skilllist_file.write(skilllist)
