from datetime import datetime, timedelta
import time
from unittest import result
from click import prompt
from flask import Flask, render_template, request,session, redirect, url_for
import joblib
import markdown
from numpy.ma import count
import pandas as pd
from pandas.plotting import table
from firebase_config import db, auth
from config import Config
from groq_client import ask_ai
from flask import jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY
@app.template_filter("datetimeformat")
def datetimeformat(value):
    try:
        return datetime.fromtimestamp(float(value)).strftime("%d %b %Y, %I:%M %p")
    except:
        return "N/A"

#Load the trained data
model = joblib.load(Config.MODEL_PATH)

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- LOGIN ----------------
@app.route("/login")
def login():
    firebase_config = {
        "apiKey": Config.FIREBASE_API_KEY,
        "authDomain": Config.FIREBASE_AUTH_DOMAIN,
        "projectId": Config.FIREBASE_PROJECT_ID,
        "storageBucket": Config.FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": Config.FIREBASE_MESSAGING_SENDER_ID,
        "appId": Config.FIREBASE_APP_ID,
        "measurementId": Config.FIREBASE_MEASUREMENT_ID,
    }

    return render_template(
        "login.html",
        firebase_config=firebase_config
    )

# ---------------- VERIFY FIREBASE TOKEN ----------------
@app.route("/verify-token", methods=["POST"])
def verify_token():

    try:
        data = request.get_json()

        if not data or "token" not in data:
            return jsonify({
                "success": False,
                "message": "Token missing"
            }), 400

        token = data["token"]

        # Verify Firebase ID token
        decoded_token = auth.verify_id_token(token)

        uid = decoded_token["uid"]
        email = decoded_token.get("email", "")

        # Get user from Firestore
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({
                "success": False,
                "message": "User details not found."
            }), 404

        user_data = user_doc.to_dict()

        # Check if the user account is blocked
        if user_data.get("blocked", False):
            return jsonify({
                "success": False,
                "message": "Your account has been blocked due to fraudulent activity."
    }), 403

        # Create Flask session
        session["uid"] = uid
        session["email"] = email
        session["name"] = user_data.get("name", "")
        session["role"] = user_data.get("role", "user")

        return jsonify({
            "success": True,
              "message": "Login successful",
            "redirect": "/dashboard"
        })

    except Exception as e:

        print("VERIFY TOKEN ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Invalid or expired Firebase token"
        }), 401
    
# ---------------- PREDICT PAGE ----------------
@app.route("/predict")
def predict():
    return render_template("predict.html")

# ---------------- PREDICTION ----------------

@app.route("/predict", methods=["POST"])
def prediction():

    if "uid" not in session:
        return redirect("/login")

    try:
        # =====================================================
        # GET INPUT VALUES
        # =====================================================

        values = []
        # Time
        values.append(float(request.form["Time"]))
        # V1 - V28
        for i in range(1, 29):
            values.append(float(request.form[f"V{i}"]))

        # Amount
        values.append(float(request.form["Amount"]))

        # CREATE DATAFRAME
        expected_columns = [
            "Time",
            "V1", "V2", "V3", "V4", "V5",
            "V6", "V7", "V8", "V9", "V10",
            "V11", "V12", "V13", "V14", "V15",
            "V16", "V17", "V18", "V19",
            "V20", "V21", "V22", "V23", "V24",
            "V25", "V26", "V27", "V28",
            "Amount"
        ]

        input_data = pd.DataFrame([values],columns=expected_columns)

        # =====================================================
        # MACHINE LEARNING PREDICTION
        # =====================================================

        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]

        # =====================================================
        # GET CLASS PROBABILITIES
        # =====================================================

        fraud_probability = 0.0
        genuine_probability = 0.0

        for class_value, probability_value in zip(
            model.classes_,probabilities):

            if class_value == 1:
                fraud_probability = round(
                    probability_value * 100,
                    2
                )

            elif class_value == 0:
                genuine_probability = round(
                    probability_value * 100,
                    2 )


        # =====================================================
        # PREDICTION LABEL
        # =====================================================

        if prediction == 1:
            prediction_label = "Fraud"

        else:
            prediction_label = "Genuine"


        # =====================================================
        # RISK LEVEL
        # =====================================================

        if fraud_probability >= 80:
            risk = "High"

        elif fraud_probability >= 50:
            risk = "Medium"

        else:
            risk = "Low"


        # =====================================================
        # AI EXPLANATION
        # =====================================================

        prompt = f"""
You are an AI assistant for a credit card fraud detection system.

A trained Random Forest machine-learning model has analyzed
ONE transaction.

The machine-learning model has already made the prediction.

Do NOT change the prediction.

Do NOT invent additional fraud indicators.

Explain the result in simple language that an ordinary user
can understand.

Transaction Amount:
{request.form["Amount"]}

Prediction:
{prediction_label}

Fraud Probability:
{fraud_probability}%

Genuine Probability:
{genuine_probability}%

Risk Level:
{risk}

Create a short professional explanation.

Use these sections:

# 🔎 Transaction Result

Explain whether the transaction was classified as
Genuine or Fraud.

# 📊 Probability

Explain the fraud and genuine probabilities.

# ⚠️ Risk Level

Explain what the risk level means.

# 🛡️ Recommended Action

If Genuine:
Recommend normal monitoring.

If Fraud:
Recommend verifying the transaction and contacting
the bank/card issuer if the transaction is unauthorized.

IMPORTANT:

- Use simple English.
- Do not use complicated mathematical terms.
- Do not claim that the model is 100% correct.
- Do not expose V1-V28 values.
- Do not invent reasons that are not provided.
- Maximum 150 words.
"""


        # =====================================================
        # CALL AI
        # =====================================================

        try:

            ai_report = ask_ai(prompt)
            ai_report = markdown.markdown(ai_report)

        except Exception as e:
            print("======================================")
            print("❌ AI EXPLANATION ERROR")
            print("Error:", str(e))
            print("======================================")


            # AI failure should NOT stop prediction
            if prediction_label == "Fraud":
                ai_report = markdown.markdown(
                    f"""
                    # 🔎 Transaction Result

                    The machine-learning model classified this
                    transaction as **Fraud**.

                    # 📊 Probability

                    **Fraud Probability:** {fraud_probability}%

                    **Genuine Probability:** {genuine_probability}%

                    # ⚠️ Risk Level

                    **{risk} Risk**

                    # 🛡️ Recommended Action

                    Please verify this transaction. If you do not
                    recognize it, contact your bank or card issuer
                    immediately.
                    """
                )

            else:

                ai_report = markdown.markdown(
                    f"""
                    # 🔎 Transaction Result

                    The machine-learning model classified this
                    transaction as **Genuine**.

                    # 📊 Probability

                    **Fraud Probability:** {fraud_probability}%

                    **Genuine Probability:** {genuine_probability}%

                    # ⚠️ Risk Level

                    **{risk} Risk**

                    # 🛡️ Recommended Action

                    The transaction appears to have a low fraud
                    probability. Continue monitoring your
                    transactions normally.
                    """
                )


        # =====================================================
        # SAVE TO FIREBASE
        # =====================================================

        db.collection("transactions").add({
            "uid": session["uid"],
            "amount": float(
                request.form["Amount"]),
            "time": float(
                request.form["Time"]),

            "prediction": prediction_label,
            "fraud_probability":fraud_probability,
            "genuine_probability":genuine_probability,
            "probability":fraud_probability,
            "risk_level":risk,
            "created_at":time.time()
        })
        print("======================================")
        print("✅ ML TRANSACTION PREDICTION")
        print("Prediction:", prediction_label)
        print("Fraud Probability:", fraud_probability)
        print("Genuine Probability:", genuine_probability)
        print("Risk:", risk)
        print("======================================")


        # =====================================================
        # RESULT PAGE
        # =====================================================

        return render_template(
            "result.html",
            prediction=prediction,
            prediction_label=prediction_label,
            probability=(
                fraud_probability
                if prediction == 1
                else genuine_probability
            ),

            fraud_probability=fraud_probability,
            genuine_probability=genuine_probability,
            risk=risk,
            amount=float(request.form["Amount"]),
            ai_report=ai_report
        )


    except ValueError:
        return """
        <div style="text-align:center; margin-top:100px;">
            <h2>❌ Invalid Input</h2>
            <p>
                Please enter valid numerical values
                for all transaction fields.
            </p>
            <a href="/predict">
                Go Back
            </a>
        </div>
        """


    except Exception as e:
        print("======================================")
        print("❌ PREDICTION ERROR")
        print("Error:", str(e))
        print("======================================")

        return f"""
        <div style="text-align:center; margin-top:100px;">

            <h2>❌ Prediction Error</h2>

            <p>
                Something went wrong while analyzing
                the transaction.
            </p>

            <a href="/predict">
                Try Again
            </a>
        </div>
        """

# ---------------- SINGLE TRANSACTION ----------------
@app.route("/single-transaction", methods=["GET", "POST"])
def single_transaction():

    if "uid" not in session:
        return redirect("/login")

    # Open the form page
    if request.method == "GET":
        return render_template("single_transaction.html")
    print("FORM DATA:", request.form)   # ← HERE


    # ---------------- USER INPUT ----------------

    transaction_id = request.form["transaction_id"]
    amount = float(request.form["amount"])
    location = request.form["location"]
    transaction_type = request.form["transaction_type"]
    failed_logins = int(request.form["failed_logins"])
    device = request.form["device_status"]
    account_age = int(request.form["account_age"])
    card_status = request.form["card_status"]

    # ---------------- RISK SCORE ----------------

    score = 0
    reasons = []

    if amount >= 50000:
        score += 30
        reasons.append("Large transaction amount")

    if failed_logins >= 3:
        score += 20
        reasons.append("Multiple failed login attempts")

    if device == "New":
        score += 15
        reasons.append("Transaction from a new device")

    if account_age < 30:
        score += 15
        reasons.append("Very new account")

    if card_status == "Not Present":
        score += 10
        reasons.append("Card-not-present transaction")

    if transaction_type in ["International", "Crypto"]:
        score += 10
        reasons.append("High-risk transaction type")

    # ---------------- RESULT ----------------

    if score >= 60:
        prediction = "Fraud"
        risk = "High"
    elif score >= 35:
        prediction = "Suspicious"
        risk = "Medium"
    else:
        prediction = "Genuine"
        risk = "Low"

    probability = min(score, 99)
    # Block user if fraud is detected
    if prediction == "Fraud":
        db.collection("users").document(session["uid"]).update({
        "blocked": True,
        "blocked_reason": "Fraudulent transaction detected",
        "blocked_at": time.time()
    })

    session.clear()

    return redirect("/blocked")

    # ---------------- AI EXPLANATION ----------------

    prompt = f"""
Explain this fraud detection result in simple English.

Transaction ID: {transaction_id}
Prediction: {prediction}
Risk Level: {risk}
Risk Score: {probability}%

Reasons:
{', '.join(reasons) if reasons else 'No major risk indicators'}

Keep it under 120 words.
"""

    try:
        ai_report = markdown.markdown(ask_ai(prompt))
    except:
        ai_report = markdown.markdown(
            f"""
# Summary

**Prediction:** {prediction}

**Risk Level:** {risk}

The decision was made using the rule-based fraud detection engine based on the transaction details provided.
"""
        )

    # ---------------- SAVE TO FIREBASE ----------------

    db.collection("transactions").add({
        "uid": session["uid"],
        "transaction_id": transaction_id,
        "amount": amount,
        "location": location,
        "prediction": prediction,
        "probability": probability,
        "risk": risk,
        "analysis_type": "Single Transaction",
        "created_at": time.time()
    })

    return render_template(
        "single_result.html",
        transaction_id=transaction_id,
        amount=amount,
        transaction_type=transaction_type,
        failed_logins=failed_logins,
        device_status=device,
        account_age=account_age,
        card_status=card_status,
        prediction=prediction,
        risk_score=score,
        risk_level=risk,
        blocked=False,
        reasons=reasons,
        ai_report=ai_report
    )
      

#---------------- CHATBOT ----------------
@app.route("/chat")
def chat():
    if "uid" not in session:
        return redirect("/login")

    return render_template("chatbot.html")

#---------------- ASK AI ----------------
@app.route("/ask-ai", methods=["POST"])
def ask_ai_route():

    if "uid" not in session:
        return jsonify({"answer": "Please login first."})
    question = request.json["question"]
    answer = ask_ai(question)
    return jsonify({
        "answer": answer
    })

# ---------------- USER REGISTRATION ----------------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        user = auth.create_user(
            email=email,
            password=password
        )
        db.collection("users").document(user.uid).set({
            "name": name,
            "email": email,
            "role": "user",
            "blocked": False,
        })

        return redirect("/login")
    return render_template("register.html")

#------------------Logout----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

#-----------------CSV UPLOAD---------------------
@app.route("/upload")
def upload():

    if "uid" not in session:
        return redirect("/login")
    return render_template("upload.html")

#--------CSV / EXCEL UPLOAD + ML / AI ANALYSIS-------------
@app.route("/upload", methods=["POST"])
def upload_file():
    if "uid" not in session:
        return redirect("/login")
    # =====================================================
    # 1. GET FILE
    # =====================================================

    file = request.files.get("file")
    if not file or file.filename == "":
        return "Please select a file."
    filename = file.filename.lower()

    
    #------------2. READ FILE----------------
    try:
        if filename.endswith(".csv"):
            data = pd.read_csv(file)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            data = pd.read_excel(file)

        else:
            return """
            <h3>Unsupported File Format</h3>
            <p>Please upload a CSV, XLS or XLSX file.</p>
            """
    except Exception as e:
        print("======================================")
        print("❌ FILE READ ERROR")
        print("Error:", str(e))
        print("======================================")

        return f"""
        <h3>Unable to Read File</h3>
        <p>{str(e)}</p>
        """
    print("======================================")
    print("✅ FILE READ COMPLETE")
    print("Filename:", file.filename)
    print("Rows:", len(data))
    print("Columns:", list(data.columns))
    print("======================================")

    # =====================================================
    # 3. EMPTY DATASET CHECK
    # =====================================================

    if data.empty:
        return """
        <h3>Empty Dataset</h3>
        <p>The uploaded file does not contain any records.</p>
        """

    # =====================================================
    # 4. LIMIT DATASET
    # =====================================================

    MAX_ROWS = 5000
    rows_limited = False
    if len(data) > MAX_ROWS:
        data = data.head(MAX_ROWS)
        rows_limited = True

    # =====================================================
    # 5. EXPECTED ML FEATURES
    # =====================================================

    expected_columns = [
        "Time","V1","V2","V3","V4","V5","V6",
        "V7","V8","V9","V10","V11",
        "V12","V13", "V14", "V15", "V16",
        "V17","V18","V19","V20","V21",
        "V22","V23","V24","V25",
        "V26","V27","V28","Amount"
    ]
    # =====================================================
    # 6. CHECK ML COMPATIBILITY
    # =====================================================

    uploaded_columns = set(data.columns)
    expected_columns_set = set(expected_columns)
    missing_columns = [column
        for column in expected_columns
        if column not in uploaded_columns

    ]


    # =====================================================
    # 7. DIFFERENT DATASET → AI ANALYSIS
    # =====================================================

    if missing_columns:
        print("======================================")
        print("🤖 DIFFERENT DATASET DETECTED")
        print("🤖 ML MODEL WILL NOT BE USED")
        print("🤖 SENDING DATASET INFORMATION TO AI")
        print("======================================")


        # -------------------------------------------------
        # DATASET INFORMATION
        # -------------------------------------------------

        total = len(data)
        columns = list(data.columns)
        column_types = data.dtypes.astype(str).to_dict()
        missing_info = data.isnull().sum().to_dict()


        # -------------------------------------------------
        # NUMERICAL STATISTICS
        # -------------------------------------------------

        try:
            numeric_summary = (
                data
                .select_dtypes(include="number")
                .describe()
                .round(2)
                .to_dict()
            )

        except Exception:
            numeric_summary = {}
        # -------------------------------------------------
        # CATEGORICAL INFORMATION
        # -------------------------------------------------

        categorical_summary = {}
        try:
            categorical_columns = data.select_dtypes(
                exclude="number"
            ).columns

            for column in categorical_columns:

                categorical_summary[column] = (
                    data[column]
                    .astype(str)
                    .value_counts()
                    .head(10)
                    .to_dict()
                )

        except Exception:
            categorical_summary = {}

        # -------------------------------------------------
        # SAMPLE RECORDS
        # -------------------------------------------------

        try:
            sample_records = (
                data.head(5)
                .fillna("")
                .to_dict("records"))

        except Exception:
            sample_records = []

        # =================================================
        # AI PROMPT
        # ==========
        prompt = f"""
    You are the AI assistant of a Credit Card Fraud Detection System.

    Analyze the uploaded transaction dataset and explain the results
    in very simple language that an ordinary user can understand.

    Do NOT use technical programming terms such as:
    - object
    - float64
    - int64
    - dataframe
    - dtype
    - Python
    - machine learning terminology unless it is necessary

    Dataset Information:

    Number of Transactions:
    {len(data)}

    Columns:
    {list(data.columns)}

    Column Data Types:
    {data.dtypes.to_dict()}

    Missing Values:
    {data.isnull().sum().to_dict()}

    Sample Records:
    {data.head(5).to_dict("records")}

    Your task is to provide a simple and professional fraud-analysis report.

    Use the following sections:

    # 📊 Dataset Overview

    Explain:
    - How many transactions were analyzed
    - What kind of information the dataset contains
    - Explain the important columns in simple language

    For example:
    Instead of saying:
    "Weight is float64"

    Say:
    "Transaction Amount represents the amount of money involved in each transaction."

    # 🔎 Transaction Analysis

    Explain:
    - Common transaction types
    - Typical transaction amounts
    - Any unusual transaction amounts
    - Any noticeable patterns

    # 🚨 Possible Fraud Indicators

    Identify patterns that MAY indicate suspicious activity.

    Examples:
    - unusually large transaction amounts
    - unusual transaction types
    - repeated transactions
    - unusual customer or merchant activity
    - unusually high number of transactions

    IMPORTANT:
    Do NOT say that a transaction is definitely fraudulent unless
    the dataset contains an actual fraud label.

    Use phrases such as:
    "may indicate suspicious activity"
    "could require further investigation"
    "appears unusual"

    # 📈 Fraud Information

    If the dataset contains a column that appears to represent
    fraud status, explain:

    - Number of legitimate transactions
    - Number of fraudulent transactions
    - Fraud percentage

    If there is no fraud information available, clearly say:

    "The dataset does not contain confirmed fraud labels, so
    individual transactions cannot be confirmed as fraudulent."

    # 🛡️ Recommendations

    Give simple recommendations for reducing fraud risk.

    # ✅ Conclusion

    Give a short summary that an ordinary user can understand.

    IMPORTANT RULES:

    1. Use simple English.
    2. Do not explain programming data types.
    3. Do not expose raw Python dictionaries.
    4. Do not expose dataframe information.
    5. Do not invent fraud cases.
    6. Do not claim that suspicious transactions are definitely fraud.
    7. Keep the report below 500 words.
    8. Make the report suitable for a normal banking/customer user.
    """
            # =================================================
            # CALL GROQ
            # =================================================

        try:

                print("⏳ GENERATING AI DATASET REPORT")

                ai_report = ask_ai(prompt)
                ai_report_html = markdown.markdown(ai_report)
                print("✅ AI REPORT GENERATED")

        except Exception as e:
                print("======================================")
                print("❌ GROQ ERROR")
                print("Error:", str(e))
                print("======================================")

                ai_report_html = markdown.markdown(
                    f"""
    # AI Analysis Unavailable

    The uploaded dataset was successfully
    read and analyzed locally.

    However, the AI analysis service could
    not be reached.

    **Dataset Records:** {total}

    **Columns:** {len(columns)}

    The machine-learning model was NOT used
    because this dataset does not match the
    trained model structure.
    """
                )


            # =================================================
            # SAVE UPLOAD SUMMARY
            # =================================================

        try:
                db.collection("uploads").add({
                    "uid": session["uid"],
                    "email": session.get("email","" ),
                    "filename": file.filename,
                    "total_transactions": total,
                    "fraud_transactions": 0,
                    "genuine_transactions": 0,
                    "fraud_percentage": 0,
                    "risk_level": "Not Determined",
                    "analysis_type": "AI Dataset Analysis",
                    "created_at": time.time()
                })

        except Exception as e:
                print("FIREBASE SAVE ERROR:", str(e))


            # =================================================
            # RETURN AI RESULT
            # =================================================
        return render_template(
            "csv_results.html",
                prediction_table=None,
                fraud_transactions=[],
                ai_report=ai_report_html,
                ml_prediction=False,
                rows_limited=rows_limited,
                total=total,
                fraud=0,
                genuine=0,
                fraud_percentage=0,
                risk_level="Not Determined"
            )
#-----------8. COMPATIBLE DATASET → ML MODEL-----------
    print("✅ COMPATIBLE CREDIT CARD DATASET")
    print("🤖 USING RANDOM FOREST MODEL")

    try:
        # -------------------------------------------------
        # KEEP ONLY MODEL FEATURES
        # -------------------------------------------------
        model_data = data[expected_columns].copy()
        # ------------------------------------------------
        # CONVERT EVERYTHING TO NUMERIC
        # -------------------------------------------------
        for column in expected_columns:
            model_data[column] = pd.to_numeric(
                model_data[column],
                errors="coerce")
        # -------------------------------------------------
        # CHECK INVALID VALUES
        # -------------------------------------------------
        if model_data.isnull().any().any():
            print("❌ INVALID NUMERICAL VALUES FOUND")
            return render_template(
                "csv_results.html",
                prediction_table=None,
                fraud_transactions=[],
                ai_report=markdown.markdown(
                    """
# Dataset Error

The uploaded dataset contains missing
or non-numeric values in one or more
columns required by the trained
machine-learning model.

Please clean the dataset and try again.
"""
                ),
                ml_prediction=False,
                rows_limited=rows_limited,
                total=len(data),
                fraud=0,
                genuine=0,
                fraud_percentage=0,
                risk_level="Not Determined"
            )


        # =================================================
        # ML PREDICTION
        # =================================================

        print("⏳ RUNNING RANDOM FOREST")
        predictions = model.predict(model_data)
        data["Prediction"] = predictions
        data["Prediction"] = data["Prediction"].replace({
            0: "Genuine",
            1: "Fraud"})
        print("✅ ML PREDICTION COMPLETE")


        # =================================================
        # STATISTICS
        # =================================================
        total = len(data)
        fraud = len(
            data[data["Prediction"] == "Fraud"])
        genuine = total - fraud
        average_amount = round(
            data["Amount"].mean(),2)
        maximum_amount = round(
            data["Amount"].max(),2)
        fraud_percentage = round(
            (fraud / total) * 100,2
            ) if total > 0 else 0

        # =================================================
        # RISK LEVEL
        # =================================================
        if fraud_percentage >= 20:
            risk_level = "High"
        elif fraud_percentage >= 5:
            risk_level = "Medium"
        else:
            risk_level = "Low"


        # =================================================
        # SAVE SUMMARY TO FIREBASE
        # =================================================

        try:
            db.collection("uploads").add({
                "uid": session["uid"],
                "email": session.get("email",  ""),
                "filename": file.filename,
                "total_transactions": total,
                "fraud_transactions": fraud,
                "genuine_transactions": genuine,
                "fraud_percentage": fraud_percentage,
                "average_amount": average_amount,
                "maximum_amount": maximum_amount,
                "risk_level": risk_level,
                "analysis_type": "Machine Learning",
                "created_at": time.time()
            })

            print("✅ FIREBASE SUMMARY SAVED")

        except Exception as e:

            print(
                "FIREBASE SAVE ERROR:",
                str(e)
            )


        # =================================================
        # AI EXPLANATION
        # =================================================

        prompt = f"""
You are an expert financial fraud analyst.

A trained Random Forest machine-learning
model has already analyzed a credit-card
transaction dataset.

The ML model performed the actual
Fraud/Genuine classification.

Do NOT change the results.

==================================================
RESULTS
==================================================

Total Transactions:
{total}

Fraud Transactions:
{fraud}

Genuine Transactions:
{genuine}

Fraud Percentage:
{fraud_percentage}%

Average Transaction Amount:
{average_amount}

Highest Transaction Amount:
{maximum_amount}

Overall Risk Level:
{risk_level}

==================================================

Generate a short professional Markdown report.

Include:

# Executive Summary

# Risk Level

# Key Findings

# Recommendations

# Conclusion

IMPORTANT:

- Do not create new predictions.
- Do not change the numbers.
- Do not claim AI performed the classification.
- Clearly state that Random Forest performed
  the classification.
- AI is only explaining the results.
- Keep the report below 300 words.
"""


        try:

            print("⏳ GENERATING AI REPORT")
            ai_report = ask_ai(prompt)
            ai_report_html = markdown.markdown(ai_report)

        except Exception as e:
            print("GROQ ERROR:",str(e))
            ai_report_html = markdown.markdown(

                f"""
# AI Report Unavailable

The machine-learning prediction
was completed successfully.

**Total Transactions:** {total}

**Fraud Transactions:** {fraud}

**Genuine Transactions:** {genuine}

**Fraud Percentage:** {fraud_percentage}%

**Risk Level:** {risk_level}

The AI explanation service could
not be reached.
"""
            )


        # =================================================
        # PREDICTION TABLE
        # =================================================

        prediction_table = data[
            [
                "Time",
                "Amount",
                "Prediction"
            ]
        ].to_html(
            classes=
            "table table-hover table-striped mb-0",
            index=False,
            border=0
        )


        # =================================================
        # FRAUD TRANSACTIONS
        # =================================================

        fraud_transactions = data[
            data["Prediction"] == "Fraud"
        ].sort_values(
            by="Amount",
            ascending=False
        ).head(20).to_dict(
            "records"
        )
        
        session["total"] = total
        session["fraud"] = fraud
        session["genuine"] = genuine
        session["fraud_percentage"] = fraud_percentage
        session["risk_level"] = risk_level

        


        # =================================================
        # RETURN ML RESULTS
        # =================================================

        return render_template(
            "csv_results.html",
            prediction_table=prediction_table,
            fraud_transactions=fraud_transactions,
            ai_report=ai_report_html,
            ml_prediction=True,
            rows_limited=rows_limited,
            total= total,
            fraud=fraud,
            genuine=genuine,
            fraud_percentage=fraud_percentage,
            risk_level=risk_level
        )
    except Exception as e:

        print("======================================")
        print("❌ ML PROCESSING ERROR")
        print("Error Type:", type(e).__name__)
        print("Error:", str(e))
        print("======================================")

        return render_template(
            "csv_results.html",
            prediction_table=None,
            fraud_transactions=[],
            ai_report=markdown.markdown(
                f"""
# Machine Learning Processing Error

The dataset appeared to match the
trained model structure, but an error
occurred during processing.

**Error:**

{str(e)}

Please verify that the dataset contains
valid numerical values.
"""
            ),

            ml_prediction=False,
            rows_limited=rows_limited,
            total=len(data),fraud=0,
            genuine=0,
            fraud_percentage=0,
            risk_level="Not Determined"
        )

#---------------- REDIRECT USER ----------------
@app.route("/redirect")
def redirect_user():

    if "uid" not in session:
        return redirect("/login")

    if session["role"] == "admin":
        return redirect("/admin")
    
    return redirect("/dashboard")

#-------------------Report generator------------
from flask import send_file
from report_generator import generate_report
import tempfile

@app.route("/download-report")
def download_report():

    summary = {
        "total": session["total"],
        "fraud": session["fraud"],
        "genuine": session["genuine"],
        "fraud_percentage": session["fraud_percentage"],
        "risk_level": session["risk_level"]
    }

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    generate_report(temp.name, summary)

    return send_file(
        temp.name,
        as_attachment=True,
        download_name="Fraud_Prediction_Report.pdf"
    )

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if "uid" not in session:
        return redirect("/login")

    uid = session["uid"]

    try:

        # ==========================================
        # GET USER INFORMATION
        # ==========================================

        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return "User information not found", 404
        user_data = user_doc.to_dict()


        # ==========================================
        # GET USER TRANSACTIONS
        # ==========================================

        transactions_query = (
            db.collection("transactions")
            .where("uid", "==", uid)
            .stream()
        )

        transactions = []

        for transaction in transactions_query:
            transaction_data = transaction.to_dict()
            transactions.append(transaction_data)

        # ==========================================
        # CALCULATE ALL STATISTICS
        # ==========================================

        total = len(transactions)

        fraud = sum(
            1
            for transaction in transactions
            if transaction.get("prediction") == "Fraud"
        )

        suspicious = sum(
            1
            for transaction in transactions
            if transaction.get("prediction") == "Suspicious"
        )

        genuine = sum(
            1
            for transaction in transactions
            if transaction.get("prediction") == "Genuine"
        )


        # ==========================================
        # FRAUD PERCENTAGE
        # ==========================================

        fraud_percentage = round(
            (fraud / total) * 100,
            2
        ) if total > 0 else 0


        # ==========================================
        # SORT BY MOST RECENT
        # ==========================================

        transactions.sort(
            key=lambda x: x.get("created_at", 0),
            reverse=True
        )


        # ==========================================
        # SHOW ONLY 50 RECENT TRANSACTIONS
        # ==========================================

        recent_transactions = transactions[:50]


        # ==========================================
        # OVERALL RISK LEVEL
        # ==========================================

        if fraud_percentage >= 20:
            risk_level = "High"

        elif fraud_percentage >= 5:
            risk_level = "Medium"

        else:
            risk_level = "Low"


        # ==========================================
        # RETURN DASHBOARD
        # ==========================================

        return render_template(
            "dashboard.html",
            name=user_data.get("name",session.get("name", "User")),
            total=total,
            fraud=fraud,
            suspicious=suspicious,
            genuine=genuine,
            fraud_percentage=fraud_percentage,
            risk_level=risk_level,
            transactions=recent_transactions
        )


    except Exception as e:

        print("======================================")
        print("❌ DASHBOARD ERROR")
        print("Error:", str(e))
        print("======================================")

        return render_template(
            "dashboard.html",
            name=session.get("name", "User"),
            total=0,
            fraud=0,
            suspicious=0,
            genuine=0,
            fraud_percentage=0,
            risk_level="Not Determined",
            transactions=[],
            error="Unable to load dashboard data",

            # GRAPH DATA
            chart_data={
                "fraud": fraud,
                "genuine": genuine,
                "suspicious": suspicious
            }
        )
    
#------------------ AI ASSISTANT ----------------
@app.route("/ai-assistant")
def ai_assistant():

    if "uid" not in session:
        return redirect("/")

    return render_template("chatbot.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin():

    if "uid" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return redirect("/dashboard")

    # Get all users
    users = []
    for doc in db.collection("users").stream():
        data = doc.to_dict()
        data["uid"] = doc.id
        users.append(data)

    # Get latest transactions
    transactions = []
    for doc in (
        db.collection("transactions")
        .order_by("created_at", direction="DESCENDING")
        .limit(100)
        .stream()
    ):
        data = doc.to_dict()
        transactions.append({
            "email": data.get("email", "N/A"),
            "Time": data.get("time", "N/A"),
            "Amount": data.get("amount", "N/A"),
            "Prediction": data.get("prediction", "N/A")
        })

    return render_template(
        "admin.html",
        users=users,
        transactions=transactions
    )

#------------------ BLOCKED PAGE ----------------
@app.route("/blocked")
def blocked():

    return render_template("blocked.html")

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
