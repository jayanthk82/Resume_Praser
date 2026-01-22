from mindee import  product  #type: ignore

def parse_resume_with_mindee(file_path, mindee_client):
    # 1. Initialize the Client

    # 2. Load the PDF file
    input_doc = mindee_client.source_from_path(file_path)

    try:
        # 3. Parse the document using the ResumeV1 product
        # Note: If your account uses a Custom Resume Model, use 'product.CustomV1' instead
        response = mindee_client.parse(product.ResumeV1, input_doc)

        # 4. Extract specific fields from the prediction
        prediction = response.document.inference.prediction

        # --- Basic Info ---
        full_name = prediction.names[0].value if prediction.names else "N/A"
        email = prediction.email_addresses[0].value if prediction.email_addresses else "N/A"
        phone = prediction.phone_numbers[0].value if prediction.phone_numbers else "N/A"
        
        # --- Professional Info ---
        # "job_titles" usually returns a list of detected roles
        job_titles = [job.value for job in prediction.job_titles]
        
        # "languages" - detected languages known
        languages = [lang.value for lang in prediction.languages]
        
        # --- Output the Data ---
        print("=== Resume Extraction Results ===")
        print(f"Name: {full_name}")
        print(f"Email: {email}")
        print(f"Phone: {phone}")
        print(f"Detected Roles: {', '.join(job_titles)}")
        print(f"Languages: {', '.join(languages)}")
        
        # Return the full prediction object if you need more raw data
        return prediction

    except Exception as e:
        print(f"Error parsing resume: {e}")
        return None
