@app.post("/chat")
def chat(request: ChatRequest):
    try:
        user_input = request.message.strip()

        # --- STEP 1: Get latest info from Google Search ---
        search_url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={GOOGLE_SEARCH_API_KEY}&cx={GOOGLE_SEARCH_ENGINE_ID}&q={user_input}"
        )
        search_response = requests.get(search_url)
        data = search_response.json()

        if "items" in data:
            snippets = " ".join([item["snippet"] for item in data["items"][:3]])
        else:
            snippets = "No recent information found online."

        # --- STEP 2: Ask Gemini for an answer ---
        prompt = f"""
        Question: {user_input}
        Context from Google Search: {snippets}
        Please answer accurately as of 2025 in clear, simple English.
        """

        result = client.models.generate_content(
            model="gemini-1.5-flash-latest",  # ✅ Updated model name
            contents=prompt
        )

        return {"response": result.output_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
