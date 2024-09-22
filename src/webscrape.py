import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import logging
import boto3
from botocore.exceptions import ClientError
from io import StringIO

# Function to fetch the webpage content
def fetch_webpage(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

# Function to extract Q&A pairs from the webpage
def extract_qa_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # List to store extracted questions and answers
    qa_pairs = []

    # Regular expressions for different question formats
    q_num_pattern = re.compile(r'Q\.\d+.*')  # Matches Q.7 or similar formats
    numbered_pattern = re.compile(r'^\d+\..*')  # Matches 2. Define... or similar formats

    # Extract all text blocks from the webpage
    paragraphs = soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'strong'])

    question = None
    answer = []

    for para in paragraphs:
        text = para.get_text(strip=True)

        # Match questions starting with "Q.<number>" or "<number>."
        if q_num_pattern.match(text) or numbered_pattern.match(text) or para.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'strong']:
            # Save the previous Q&A pair
            if question and answer:
                qa_pairs.append((question, ' '.join(answer).strip()))
                answer = []

            # New question detected
            question = text
        else:
            # Append paragraph to the current answer
            answer.append(text)

    # Add the last Q&A pair if any
    if question and answer:
        qa_pairs.append((question, ' '.join(answer).strip()))

    return qa_pairs

# Function to store Q&A pairs in a DataFrame
def store_in_dataframe(qa_pairs):
    df = pd.DataFrame(qa_pairs, columns=['Question', 'Answer'])
    return df

# Main function
def main(url):
    html_content = fetch_webpage(url)

    if html_content:
        qa_pairs = extract_qa_from_html(html_content)
        qa_df = store_in_dataframe(qa_pairs)
        return qa_df
    else:
        print("Failed to retrieve the webpage.")
        return None



def upload_df_to_s3_folder(df, bucket_name, folder_name, file_name):
    s3_client = boto3.client('s3')
    
    # Combine folder and file name to create the S3 key
    s3_key = f"{folder_name}/{file_name}"
    
    # Convert DataFrame to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # Upload to S3
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=csv_buffer.getvalue()
        )
        print(f"File {file_name} uploaded successfully to {bucket_name}/{folder_name}")
        return True
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False
    


'''url = "https://www.geeksforgeeks.org/sql-interview-questions/"
qa_df = main(url)
s3_bucket = "mock-interview-webscrape-a"
folder = "webscraped_generic"
file_name="gfg.csv"

if qa_df is not None:
    print(qa_df)
    upload_df_to_s3_folder(qa_df, s3_bucket, folder, file_name)

'''
def handler(event, context):
    url = "https://www.geeksforgeeks.org/sql-interview-questions/"
    qa_df = main(url)
    s3_bucket = "mock-interview-webscrape-a"
    folder = "webscraped_generic"
    file_name="gfg.csv"

    if qa_df is not None:
        print(qa_df)
        upload_df_to_s3_folder(qa_df, s3_bucket, folder, file_name)

    return {
        'statusCode': 200,
        'body': "Uploaded"
    }



