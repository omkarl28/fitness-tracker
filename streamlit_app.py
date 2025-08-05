import streamlit as st
import pandas as pd
import numpy as np
import datetime
import sqlite3
import plotly.express as px
 
st.set_page_config(layout="wide")
# Hardcoded user data
users = {
    "Omkar": {"height_cm": 177.8, "age": 37},   # 5'10" = 177.8 cm
    "Prutha": {"height_cm": 167.6, "age": 31}   # 5'6" = 167.6 cm
}

# SQLite setup
conn = sqlite3.connect("getfit.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS daily_input (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    date TEXT,
    weight REAL,
    workout_done INTEGER,
    diet_done INTEGER,
    slept_7h INTEGER,
    drank_water INTEGER,
    water_needed REAL
)
""")
conn.commit()

# Sidebar navigation
st.sidebar.title("GetFit App")
page = st.sidebar.radio("Go to", ["Home", "Daily Input", "Nutrition", "Grocery List","Workout"])

def calculate_bmi(weight, height_cm):
    if not weight or not height_cm:
        return None
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)

if page == "Home":
    
   

    df = pd.read_sql("SELECT * FROM daily_input", conn)
    if not df.empty:
        st.subheader("90-Day Challenge Progress")
        challenge_days = 90
        challenge_start = pd.to_datetime(df["date"].min())
        challenge_end = challenge_start + pd.Timedelta(days=challenge_days-1)
        today = pd.to_datetime(datetime.date.today())
        days_remaining = max(0, (challenge_end - today).days + 1)
        total_days = (challenge_end - challenge_start).days + 1
        days_passed = (today - challenge_start).days + 1
        progress = min(max(days_passed / total_days, 0), 1)

        # Progress bar with labels
        st.markdown(
            f"<div style='display: flex; justify-content: space-between;'>"
            f"<span>Start: <b>{challenge_start.strftime('%Y-%m-%d')}</b></span>"
            f"<span>End: <b>{challenge_end.strftime('%Y-%m-%d')}</b></span>"
            f"</div>",
            unsafe_allow_html=True
        )
        st.progress(progress)
        st.write(f"**Days Remaining:** {days_remaining}")
        col1, col2 = st.columns(2)
        with col1:
            start_weight=94.6
            df_prutha = pd.read_sql("SELECT * FROM daily_input where user='Prutha'", conn)
            target_weight = 82.0  # Example target weight for Prutha
            height=167.64  # Example height for Prutha in cm
            target_bmi =  round(target_weight / ((height / 100) ** 2), 2)
            if not df_prutha.empty:
                    prutha_weight = df_prutha["weight"].iloc[-1]
                    prutha_bmi = calculate_bmi(prutha_weight, users["Prutha"]["height_cm"])
                    st.metric(f"Prutha's Weight (Target: {target_weight})", f"{prutha_weight:.1f} kg", delta=f"{prutha_weight - target_weight:.1f} kg Remaining Weightloss")
                    weight_loss_percent = ((start_weight - prutha_weight) / (start_weight - target_weight)) * 100
                    st.write(f"**Weight Loss Progress:** {weight_loss_percent:.2f}%")
                    
                    st.metric("Prutha's BMI", f"{prutha_bmi:.2f}", delta=f"{prutha_bmi - target_bmi:.2f} BMI Remaining BMI Reduction")
                    

                    
        with col2:
            start_weight=90.6
            df_omkar = pd.read_sql("SELECT * FROM daily_input where user='Omkar'", conn)
            target_weight = 80.0
            height=180.8  # Example height for Omkar in cm
            target_bmi =  round(target_weight / ((height / 100) ** 2), 2)
            if not df_omkar.empty:
                omkar_weight = df_omkar["weight"].iloc[-1]
                omkar_bmi = calculate_bmi(omkar_weight, users["Omkar"]["height_cm"])
                st.metric(f"Omkar's Weight (Target: {target_weight})", f"{omkar_weight:.1f} kg", delta=f"{omkar_weight - target_weight:.1f} kg Remaining Weightloss")
                weight_loss_percent = ((start_weight - omkar_weight) / (start_weight - target_weight)) * 100
                st.write(f"**Weight Loss Progress:** {weight_loss_percent:.2f}%")
                
                st.metric("Omkar's BMI", f"{omkar_bmi:.2f}", delta=f"{omkar_bmi - target_bmi:.2f} BMI Remaining BMI Reduction")
        # Aggregate to ensure one weight per user per date (take last entry if duplicates)
        df_plot = (
            df.sort_values("date")
            .groupby(["user", "date"], as_index=False)
            .last()
        )

        # Add a text column for labels
        df_plot["weight_label"] = df_plot["weight"].round(1).astype(str)

        fig = px.line(
            df_plot,
            x="date",
            y="weight",
            color="user",
            title="Weight Progress Over Time",
            markers=True,
            text="weight_label"
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Weight (kg)",
            legend_title="User",
            xaxis=dict(tickformat="%Y-%m-%d"),
        )
        st.plotly_chart(fig, use_container_width=True)

# ...existing code...

elif page == "Daily Input":
    st.title("Daily Input")
    user = st.selectbox("Select User", ["Omkar", "Prutha"])
    today = datetime.date.today()
    weight_today = st.number_input("Weight today (kg)", min_value=30.0, max_value=200.0, step=0.1)
    st.write(f"Height: {users[user]['height_cm']/2.54:.0f} inches ({users[user]['height_cm']} cm)")
    workout_done = st.checkbox("Workout done today?")
    diet_done = st.checkbox("Diet followed today?")
    slept_7h = st.checkbox("Slept >7 hours?")
    water_needed_l = weight_today * 0.035 if weight_today else 0
    drank_water = st.checkbox(f"Drank at least {water_needed_l:.2f} liters of water today?")
    st.write(f"Recommended water intake: {water_needed_l:.2f} liters")

    if st.button("Submit"):
        c.execute("""
            INSERT INTO daily_input (user, date, weight, workout_done, diet_done, slept_7h, drank_water, water_needed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user, str(today), weight_today, int(workout_done), int(diet_done), int(slept_7h), int(drank_water), water_needed_l
        ))
        conn.commit()
        st.success("Entry submitted!")

# ...existing code...


import json

# --- Nutrition DB Setup ---
c.execute("""
CREATE TABLE IF NOT EXISTS meal_plan (
    day TEXT PRIMARY KEY,
    wakeup_drink TEXT,
    breakfast TEXT,
    mid_morning_snack TEXT,
    lunch TEXT,
    snack TEXT,
    dinner TEXT
)
""")
conn.commit()

default_meal_plan_rows = [
    ("Monday", "Warm water + soaked almonds/walnuts",
     "[Masala Omelette (2 eggs)](https://www.indianhealthyrecipes.com/masala-omelette-recipe/) + 1 Multigrain Toast + 1 Fruit (like apple or banana)",
     "Apple + green tea",
     "[Grilled Chicken Breast+Rice+Salad](https://www.indianhealthyrecipes.com/grilled-chicken/)",
     "Buttermilk + roasted chana",
     "[Grilled Chicken Breast+Rice+Salad](https://www.indianhealthyrecipes.com/grilled-chicken/)"),
    ("Tuesday", "Warm water + soaked almonds/walnuts",
     "[Idli (2) + sambar](https://www.indianhealthyrecipes.com/idli-sambar-recipe/)",
     "Sprouts + guava",
     "[Brown rice + paneer + veg + salad (veg day)](https://www.indianhealthyrecipes.com/paneer-curry/)",
     "Boiled egg + tea",
     "[Brown rice + paneer + veg + salad (veg day)](https://www.indianhealthyrecipes.com/paneer-curry/)"),
    ("Wednesday", "Warm water + soaked almonds/walnuts",
     "[Masala Omelette (2 eggs)](https://www.indianhealthyrecipes.com/masala-omelette-recipe/) + 1 Multigrain Toast + 1 Fruit (like apple or banana)",
     "Green tea + 2 khakras",
     "[Chicken Tikka (Tandoori-style, boneless)+Rice+Salad](https://www.indianhealthyrecipes.com/chicken-tikka-recipe/)",
     "1 fruit or nuts",
     "[Chicken Tikka (Tandoori-style, boneless)+Rice+Salad](https://www.indianhealthyrecipes.com/chicken-tikka-recipe/)"),
    ("Thursday", "Warm water + soaked almonds/walnuts",
     "[Masala Omelette (2 eggs)](https://www.indianhealthyrecipes.com/masala-omelette-recipe/) + 1 Multigrain Toast + 1 Fruit (like apple or banana)",
     "1 fruit + green tea",
     "[Chicken Curry (light oil, tomato-based)+Rice+Salad](https://www.indianhealthyrecipes.com/chicken-curry/)",
     "Green tea + 1 Egg",
     "[Chicken Curry (light oil, tomato-based)+Rice+Salad](https://www.indianhealthyrecipes.com/chicken-curry/)"),
    ("Friday", "Warm water + soaked almonds/walnuts",
     "[Masala Omelette (2 eggs)](https://www.indianhealthyrecipes.com/masala-omelette-recipe/) + 1 Multigrain Toast + 1 Fruit (like apple or banana)",
     "Sprouts or nuts",
     "[Chicken Kheema (minced chicken with peas)+Rice+Salad](https://www.indianhealthyrecipes.com/chicken-keema-recipe/)",
     "Chana or 1 egg",
     "[Chicken Kheema (minced chicken with peas)+Rice+Salad](https://www.indianhealthyrecipes.com/chicken-keema-recipe/)"),
    ("Saturday", "Warm water + soaked almonds/walnuts",
     "[Idli (2) + sambar](https://www.indianhealthyrecipes.com/idli-sambar-recipe/)",
     "1 boiled egg",
     "[Brown rice + paneer curry + veg (veg day)](https://www.indianhealthyrecipes.com/paneer-curry/)",
     "Buttermilk + almonds",
     "[Brown rice + paneer curry + veg (veg day)](https://www.indianhealthyrecipes.com/paneer-curry/)"),
    ("Sunday", "Warm water + soaked almonds/walnuts",
     "[Masala Omelette (2 eggs)](https://www.indianhealthyrecipes.com/masala-omelette-recipe/) + 1 Multigrain Toast + 1 Fruit (like apple or banana)",
     "Chana or almonds",
     "[Chicken Biryani (homemade, controlled oil)+Rice+Salad](https://www.indianhealthyrecipes.com/chicken-biryani-recipe/)",
     "Sprouts or salad",
     "[Chicken Biryani (homemade, controlled oil)+Rice+Salad](https://www.indianhealthyrecipes.com/chicken-biryani-recipe/)")
]

# Insert default meal plan if table is empty or force reset
c.execute("DELETE FROM meal_plan")
c.executemany("""
    INSERT INTO meal_plan (day, wakeup_drink, breakfast, mid_morning_snack, lunch, snack, dinner)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", default_meal_plan_rows)
conn.commit()

if page == "Nutrition":
    st.title("Nutrition Plan")
    st.info("test is your weekly meal plan. Click on meal names for recipes!")

    df_meal = pd.read_sql("SELECT * FROM meal_plan ORDER BY "
                          "CASE day "
                          "WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 "
                          "WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 WHEN 'Sunday' THEN 7 END", conn)

    st.markdown(df_meal.to_markdown(index=False), unsafe_allow_html=True)

# ...existing code...
elif page == "Grocery List":
    st.title("Grocery List Prompt Generator")
    st.info("Copy the prompt below and paste it into ChatGPT to get your grocery list.")

    # Fetch meal plan from DB
    df_meal = pd.read_sql("SELECT * FROM meal_plan ORDER BY "
                          "CASE day "
                          "WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 "
                          "WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 WHEN 'Sunday' THEN 7 END", conn)

    meal_plan_text = ""
    for idx, row in df_meal.iterrows():
        meal_plan_text += f"{row['day']}:\n"
        meal_plan_text += f"  Wake-up Drink: {row['wakeup_drink']}\n"
        meal_plan_text += f"  Breakfast: {row['breakfast']}\n"
        meal_plan_text += f"  Mid-Morning Snack: {row['mid_morning_snack']}\n"
        meal_plan_text += f"  Lunch: {row['lunch']}\n"
        meal_plan_text += f"  Snack: {row['snack']}\n"
        meal_plan_text += f"  Dinner: {row['dinner']}\n\n"

    prompt = (
        "Given the following weekly meal plan, generate a consolidated grocery shopping list for all ingredients needed. "
        "Group similar items and quantities where possible. Only output the grocery list, nothing else.\n\n"
        f"{meal_plan_text}"
    )

    st.markdown("#### Copy this prompt and paste it into ChatGPT:")
    st.code(prompt, language="markdown")
elif page == "Workout":
    st.title("Personalized Workout Plan")
    user = st.selectbox("Select User", ["Omkar", "Prutha"], key="workout_user")

    if user == "Omkar":
        st.subheader("Workout Plan for Omkar")
        st.warning("Post-vitrectomy with oil removal — avoid lifting more than 5 kg.")

        st.markdown("""
        **Focus Areas:**  
        - Light mobility  
        - Gentle walking  
        - Breathing exercises  
        - No strength or core-heavy training until medically cleared  

        **Weekly Routine (Example):**
        | Day       | Activity                     |
        |-----------|------------------------------|
        | Monday    | 20-min slow walk + stretching |
        | Tuesday   | Breathing + neck/shoulder rolls |
        | Wednesday | 20-min walk + deep breathing |
        | Thursday  | Rest or short walk            |
        | Friday    | Breathing + light yoga       |
        | Saturday  | 25-min walk                  |
        | Sunday    | Rest                         |

        **Tips:**
        - Avoid jerky head movements.
        - Wear sunglasses if light sensitive.
        - Follow doctor's post-op instructions always.
        """)

    elif user == "Prutha":
        st.subheader("Workout Plan for Prutha")
        st.info("Diabetes management — focus on consistency and moderate cardio.")

        st.markdown("""
        **Focus Areas:**  
        - Moderate-intensity cardio (walking, cycling)  
        - Resistance training (bodyweight, light dumbbells)  
        - Flexibility and relaxation  

        **Weekly Routine (Example):**
        | Day       | Activity                               |
        |-----------|----------------------------------------|
        | Monday    | 30-min brisk walk + stretching         |
        | Tuesday   | Light resistance workout (15-20 min)   |
        | Wednesday | Yoga (focus on flexibility & breath)   |
        | Thursday  | Rest / Walk after dinner (15-20 min)   |
        | Friday    | 30-min cycling or walking              |
        | Saturday  | Resistance + yoga combo (30 min)       |
        | Sunday    | Walk + breathing exercises             |

        **Tips:**
        - Monitor blood sugar before & after workouts.
        - Stay hydrated.
        - Eat a small snack if blood sugar drops.
        """)

    st.markdown("---")
    st.caption("Note: Always consult a medical professional before starting or modifying your workout routine.")
