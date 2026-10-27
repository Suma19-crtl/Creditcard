import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

console.log(window.firebaseConfig);

const app = initializeApp(window.firebaseConfig);

export const auth = getAuth(app);