from sentence_transformers import SentenceTransformer, util  #type: ignore

def calculate_match_score(user_summary: str, jd_summary: str,model) -> float:
    
    # 2. Encode the texts into embeddings (vectors)
    # convert_to_tensor=True ensures we get PyTorch tensors for efficient calculation
    embedding_profile = model.encode(user_summary, convert_to_tensor=True)
    embedding_jd = model.encode(jd_summary, convert_to_tensor=True)

    # 3. Compute Cosine Similarity
    # This measures the cosine of the angle between the two vectors.
    # 1.0 means the vectors point in the exact same direction (identical meaning).
    cosine_score = util.cos_sim(embedding_profile, embedding_jd)

    # 4. Extract the scalar value and convert to percentage
    # .item() pulls the float value out of the tensor
    score_percentage = cosine_score.item() * 100

    return round(score_percentage, 2)

