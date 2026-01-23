from typing import Dict, Any, Optional
from mindee import ClientV2, InferenceParameters, PathInput #type: ignore
from typing import Dict, Any, Optional

# Constants
# Replace this with the specific Model ID you provided if it changes
MODEL_ID = "271392a7-da72-4c28-bcd8-ca6157cdecdf"

from mindee import ClientV2, InferenceParameters, PathInput #type: ignore
from typing import Dict, Any, Optional

# Your specific Model ID
MODEL_ID = "271392a7-da72-4c28-bcd8-ca6157cdecdf"

def parse_resume_with_mindee(file_path: str, mindee_client: ClientV2) -> Optional[Dict[str, Any]]:
    """
    Parses a resume using Mindee ClientV2 and extracts data from Mindee Field objects.
    """
    try:
        # 1. Set inference parameters
        params = InferenceParameters(
            model_id=MODEL_ID,
            rag=True,
            raw_text=True,
            confidence=True
        )

        # 2. Load the file
        input_source = PathInput(file_path)

        # 3. Process
        response = mindee_client.enqueue_and_get_inference(
            input_source, params
        )

        # 4. Extract Data
        if response and response.inference and response.inference.result:
            # 'fields' is a dictionary of Mindee Field objects (SimpleField, ListField, etc.)
            fields = response.inference.result.fields
            
            # --- Helper Function to Extract Data from Mindee Objects ---
            def extract_field_value(field_obj):
                """
                Safely extracts value(s) from a Mindee Field object.
                """
                if field_obj is None:
                    return None
                
                # Case 1: ListField (Has a 'values' attribute containing a list of items)
                # Found in: experience, education, skills, languages, etc.
                if hasattr(field_obj, 'values'):
                    # Convert each item in the list to its string representation
                    return [str(item) for item in field_obj.values]

                # Case 2: SimpleField (Has a 'value' attribute)
                # Found in: name, email, phone_number, etc.
                if hasattr(field_obj, 'value'):
                    return str(field_obj.value) if field_obj.value is not None else None

                # Fallback: Stringify the object itself
                return str(field_obj)

            # --- Construct Result Dictionary ---
            # We map the keys specifically found in your 'raw_data' output
            result_data = {
                # Personal Info
                "name": extract_field_value(fields.get("name")),
                "email": extract_field_value(fields.get("email")),
                "phone": extract_field_value(fields.get("phone_number")),
                "address": extract_field_value(fields.get("address")),
                "linkedin": extract_field_value(fields.get("linkedin_profile")),
                "summary": extract_field_value(fields.get("summary_objective")),

                # Lists (Professional Info)
                "experience": extract_field_value(fields.get("experience")),
                "education": extract_field_value(fields.get("education")),
                "skills": extract_field_value(fields.get("skills")),
                "languages": extract_field_value(fields.get("languages")),
                "projects": extract_field_value(fields.get("projects")),
                "certifications": extract_field_value(fields.get("awards_certifications")),
                
                # Debugging: Show keys found to verify correctness
                "found_keys": list(fields.keys())
            }
            
            return result_data
            
        return None

    except Exception as e:
        print(f"Error parsing resume with Mindee V2: {e}")
        # Print full traceback for debugging if needed
        import traceback
        traceback.print_exc()
        return None
    

