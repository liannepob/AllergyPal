# AllergyPal 🌿

A full-stack web application for managing food allergies, emergency contacts, and safe dining.

**Live Demo:** [liannepob.pythonanywhere.com](https://liannepob.pythonanywhere.com)

## About
AllergyPal was built to solve a real problem — managing food allergies in everyday life. 
Users can track their allergies, store emergency contacts, and keep a list of safe and 
unsafe restaurants all in one place.

## Features
- User authentication (register, login, logout)
- Allergy profile with severity tracking (mild, moderate, severe)
- Emergency contacts management
- Emergency card page for medical situations
- Restaurant safety tracker (safe, unsafe, unsure)
- Dark/light mode toggle
- Flash messages and form validation

## Tech Stack
- **Backend:** Python, Flask, CS50 SQL library
- **Database:** SQLite
- **Frontend:** HTML, CSS, Jinja2
- **Auth:** Werkzeug password hashing, Flask sessions
- **Deployment:** PythonAnywhere

## Database Schema
- `users` — account info and profile
- `allergies` — global allergen master list
- `user_allergies` — many-to-many join table with severity
- `restaurants` — restaurant info
- `saved_restaurants` — user-specific restaurant safety status
- `emergency_contacts` — contacts linked to each user

## Roadmap
- [ ] Restaurant API integration (Yelp / Google Places)
- [ ] Map view for nearby safe restaurants
- [ ] Friends and social sharing
- [ ] AI-powered allergy risk scoring (CS50 AI)
- [ ] Mobile responsive design

## Setup
```bash
git clone https://github.com/liannepob/AllergyPal.git
cd AllergyPal
pip install -r requirements.txt
python3 -m flask run
```

## Author
Built by Lianne Poblador as a personal portfolio project.
