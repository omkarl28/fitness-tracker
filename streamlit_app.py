import streamlit as st
import pandas as pd
import numpy as np
import datetime
import sqlite3
 

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
    st.title("Home")
    st.header("Progress Overview")

    df = pd.read_sql("SELECT * FROM daily_input", conn)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        total_days = (df["date"].max() - df["date"].min()).days + 1

        st.subheader("Summary")
        summary_cols = st.columns(len(users))
        for idx, user in enumerate(users.keys()):
            user_df = df[df["user"] == user]
            if not user_df.empty:
                workouts_done = user_df["workout_done"].sum()
                diet_followed = user_df["diet_done"].sum()
                water_drank = user_df["drank_water"].sum()
                slept_well = user_df["slept_7h"].sum()
                days_recorded = user_df["date"].nunique()

                with summary_cols[idx]:
                    st.markdown(f"### {user}")
                    st.metric("Workouts Done", f"{workouts_done} / {total_days}")
                    st.metric("Diet Followed", f"{diet_followed} / {total_days}")
                    st.metric("Water Drank", f"{water_drank} / {total_days}")
                    st.metric("Slept Well", f"{slept_well} / {total_days}")
            else:
                with summary_cols[idx]:
                    st.markdown(f"### {user}")
                    st.info("No data.")

        # ...existing chart code...
        for user in users.keys():
            st.subheader(user)
            user_df = df[df["user"] == user].sort_values("date")
            if not user_df.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Weight (kg)**")
                    st.bar_chart(user_df.set_index("date")["weight"])
                with col2:
                    st.markdown("**BMI**")
                    user_df["bmi"] = user_df.apply(lambda row: calculate_bmi(row["weight"], users[user]["height_cm"]), axis=1)
                    st.line_chart(user_df.set_index("date")["bmi"])
                with col3:
                    st.markdown("**Sleep >7h**")
                    st.line_chart(user_df.set_index("date")["slept_7h"])
                st.markdown("**Water Intake**")
                st.line_chart(user_df.set_index("date")[["drank_water", "water_needed"]].rename(columns={"drank_water": "Drank Water (Yes=1)", "water_needed": "Water Needed (L)"}))
                st.markdown("**Workout & Diet**")
                st.line_chart(user_df.set_index("date")[["workout_done", "diet_done"]].rename(columns={"workout_done": "Workout Done", "diet_done": "Diet Followed"}))
            else:
                st.info(f"No data for {user}.")
    else:
        st.info("No data available. Please add daily input.")

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

# Default meal plan as a list of tuples for easy DB insertion
default_meal_plan_rows = [
    ("Monday", "Warm water + soaked almonds/walnuts", "2 eggs + 1 toast + sautéed spinach", "Apple + green tea", "Brown rice + grilled chicken + veg curry + salad", "Buttermilk + roasted chana", "2 rotis + chicken curry + sautéed veg"),
    ("Tuesday", "Warm water + soaked almonds/walnuts", "Idli (2) + sambar", "Sprouts + guava", "Brown rice + paneer + veg + salad (veg day)", "Boiled egg + tea", "2 rotis + paneer curry + salad (veg day)"),
    ("Wednesday", "Warm water + soaked almonds/walnuts", "Vegetable oats + almonds", "Green tea + 2 khakras", "Brown rice + chicken + steamed veg + curd", "1 fruit or nuts", "Brown rice + fish curry + steamed veg"),
    ("Thursday", "Warm water + soaked almonds/walnuts", "2 eggs + 1 toast + sautéed spinach", "1 fruit + green tea", "Brown rice + fish curry + veg + salad", "Green tea + 2 khakras", "Millet roti + tofu curry + salad"),
    ("Friday", "Warm water + soaked almonds/walnuts", "Smoothie (spinach, banana, chia)", "Sprouts or nuts", "Millet + egg curry + salad", "Chana or 1 egg", "2 rotis + egg bhurji + veg"),
    ("Saturday", "Warm water + soaked almonds/walnuts", "Idli (2) + sambar", "1 boiled egg", "Brown rice + paneer curry + veg (veg day)", "Buttermilk + almonds", "Roti + dal + bhindi (veg day)"),
    ("Sunday", "Warm water + soaked almonds/walnuts", "2 eggs + 1 toast + sautéed spinach", "Chana or almonds", "Brown rice + grilled chicken + veg + soup", "Sprouts or salad", "Brown rice + grilled chicken + soup"),
]

# Insert default meal plan if table is empty
c.execute("SELECT COUNT(*) FROM meal_plan")
if c.fetchone()[0] == 0:
    c.executemany("""
        INSERT INTO meal_plan (day, wakeup_drink, breakfast, mid_morning_snack, lunch, snack, dinner)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, default_meal_plan_rows)
    conn.commit()

if page == "Nutrition":
    st.title("Nutrition Plan")
    st.info("Edit your weekly meal plan below. Changes are saved to the database.")

    # Fetch meal plan from DB
    df_meal = pd.read_sql("SELECT * FROM meal_plan ORDER BY "
                          "CASE day "
                          "WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 "
                          "WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 WHEN 'Sunday' THEN 7 END", conn)

    edited_df = st.data_editor(
        df_meal,
        num_rows="fixed",
        use_container_width=True,
        key="meal_plan_editor"
    )

    if st.button("Save Changes"):
        for idx, row in edited_df.iterrows():
            c.execute("""
                UPDATE meal_plan SET
                    wakeup_drink = ?,
                    breakfast = ?,
                    mid_morning_snack = ?,
                    lunch = ?,
                    snack = ?,
                    dinner = ?
                WHERE day = ?
            """, (
                row["wakeup_drink"], row["breakfast"], row["mid_morning_snack"],
                row["lunch"], row["snack"], row["dinner"], row["day"]
            ))
        conn.commit()
        st.success("Meal plan updated!")

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
elif page == "Workout Plan":
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
