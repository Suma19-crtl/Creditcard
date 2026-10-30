# 💳 AI-Based Credit Card Fraud Detection System

An intelligent web-based application designed to identify potentially fraudulent credit card transactions using Machine Learning.

## 📌 About the Project

The AI-Based Credit Card Fraud Detection System aims to help identify suspicious financial transactions and distinguish between fraudulent and genuine transactions.

The application combines a Flask-based web interface with a machine learning model to analyse transaction data and generate fraud predictions.

## 🎯 Project Objectives

- Detect potentially fraudulent credit card transactions.
- Classify transactions as fraudulent or genuine.
- Analyse transaction amounts and fraud statistics.
- Present results through a web-based interface.
- Generate AI-assisted explanations and recommendations.

## ✨ Key Features

- **Fraud Detection:** Predicts whether a transaction is potentially fraudulent.
- **Machine Learning:** Uses a trained model for transaction classification.
- **Transaction Analysis:** Analyses transaction statistics and amounts.
- **Risk Explanation:** Provides explanations for transaction predictions.
- **AI-Powered Insights:** Generates analytical summaries and recommendations.
- **Report Generation:** Includes a separate report-generation module.
- **Web Interface:** Provides an interactive application through Flask.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Flask | Web application framework |
| Pandas | Data processing |
| NumPy | Numerical operations |
| Scikit-learn | Machine learning |
| Joblib | Model storage and loading |
| HTML, CSS, JavaScript | Frontend development |

## 📂 Project Structure

```text
Creditcard/
│
├── models/
├── static/
├── templates/
│
├── app.py
├── train_model.py
├── ai_service.py
├── groq_client.py
├── firebase_config.py
├── config.py
├── report_generator.py
├── utils.py
├── test_groq.py
├── requirements.txt
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Suma19-crtl/Creditcard.git
```

### 2. Open the project folder

```bash
cd Creditcard
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment

Windows:

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Add the required API credentials and configuration values using a `.env` file or the configuration method used by the application. Never upload secret keys to GitHub.

### 7. Run the application

```bash
python app.py
```

Open the local URL displayed in your terminal.

## 🧠 How It Works

1. Transaction data is provided to the application.
2. The data is processed for analysis.
3. The trained machine learning model evaluates the transaction.
4. The application displays the prediction.
5. AI-assisted analysis provides additional explanations and recommendations.

## 🔮 Future Enhancements

- Real-time transaction monitoring.
- Improved fraud detection model accuracy.
- Interactive fraud analytics dashboard.
- Email notifications for suspicious transactions.
- Advanced transaction pattern analysis.

## 👩‍💻 Author

**Suma V**

MCA Graduate | Python Developer

GitHub: https://github.com/Suma19-crtl

---

⭐ If you find this project interesting, feel free to explore the repository.
