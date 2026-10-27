from groq_client import ask_ai


def analyze_dataset(total, fraud, genuine,
                    average_amount,
                    maximum_amount,
                    fraud_percentage):

    prompt = f"""
You are an expert financial fraud analyst.

Analyze this dataset.

Total Transactions: {total}
Fraud Transactions: {fraud}
Genuine Transactions: {genuine}
Average Transaction Amount: {average_amount}
Highest Transaction Amount: {maximum_amount}
Fraud Percentage: {fraud_percentage}%

Return Markdown.

Include

# Executive Summary

# Risk Level

# Key Findings

# Recommendations

# Conclusion
"""

    return ask_ai(prompt)


def explain_transaction(prediction,
                        probability,
                        risk,
                        amount):

    prompt = f"""
You are an expert banking fraud analyst.

Prediction:
{prediction}

Confidence:
{probability}%

Risk:
{risk}

Transaction Amount:
{amount}

Explain:

# Summary

# Why it was predicted

# Risk Level

# Recommendation

Keep it under 200 words.
"""

    return ask_ai(prompt)