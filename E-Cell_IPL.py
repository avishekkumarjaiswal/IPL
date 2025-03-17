import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# Custom CSS to hide elements and make the app full-screen
st.markdown(
    """
    <style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Full-screen mode */
    .stApp {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100vw !important;
        height: 100vh !important;
    }

    /* Disable scrolling */
    body {
        overflow: hidden;
    }

    /* Custom styling for the main content */
    .main-content {
        padding: 20px;
        background-color: #f9f9f9;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to validate team balance
def validate_team(df):
    teams = df['Team'].unique()
    balance_report = {}

    for team in teams:
        squad = df[df['Team'] == team]
        foreign_count = squad[squad['Nationality'] != 'Indian'].shape[0]
        batters = squad[squad['Role'] == 'Batter'].shape[0]
        wk = squad[squad['Role'] == 'Wicketkeeper'].shape[0]
        allrounders = squad[squad['Role'] == 'Allrounder'].shape[0]
        bowlers = squad[squad['Role'] == 'Bowler'].shape[0]
        rating = squad['Rating'].mean()

        balance_report[team] = {
            'Total Players': len(squad),
            'Foreign Players': foreign_count,
            'Batters': batters,
            'Wicketkeepers': wk,
            'Allrounders': allrounders,
            'Bowlers': bowlers,
            'Average Rating': round(rating, 2),
            'Balanced': (4 <= batters <= 6) and (1 <= wk <= 2) and (2 <= allrounders <= 3) and (3 <= bowlers <= 5) and (foreign_count <= 4)
        }

    return pd.DataFrame(balance_report).T

# Function to simulate a match
def simulate_match(team1, team2, ratings, balance_report):
    team1_balanced = balance_report.loc[team1, 'Balanced']
    team2_balanced = balance_report.loc[team2, 'Balanced']

    # Adjust ratings based on balance
    team1_rating = ratings[team1] * (1.1 if team1_balanced else 0.9)
    team2_rating = ratings[team2] * (1.1 if team2_balanced else 0.9)

    # Simulate match outcome
    if team1_rating > team2_rating:
        return team1 if random.random() > 0.3 else team2
    else:
        return team2 if random.random() > 0.3 else team1

# Generate fixtures for double round-robin ensuring no team plays consecutively
def generate_fixtures(teams):
    fixtures = []
    n = len(teams)
    
    # First round: Each team plays every other team once
    for i in range(n - 1):
        for j in range(i + 1, n):
            fixtures.append(f"{teams[i]} vs {teams[j]}")
    
    # Second round: Reverse fixtures
    for i in range(n - 1):
        for j in range(i + 1, n):
            fixtures.append(f"{teams[j]} vs {teams[i]}")
    
    return fixtures

# Generate a schedule with dates and times
def generate_schedule(fixtures, start_date):
    schedule = []
    current_date = start_date
    for i, match in enumerate(fixtures):
        time = "02:00 PM GMT / 07:30 PM LOCAL" if i % 2 == 0 else "10:00 AM GMT / 03:30 PM LOCAL"
        schedule.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "Match Details": match,
            "Time": time
        })
        current_date += timedelta(days=1)
    return pd.DataFrame(schedule)

# Streamlit UI
st.title("Hindu's E-Cell Virtual IPL")

uploaded_file = st.file_uploader("Upload Team Squad CSV", type='csv')

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Initialize session state variables
    if 'balance_report' not in st.session_state:
        st.session_state.balance_report = validate_team(df)
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'points_table' not in st.session_state:
        st.session_state.points_table = pd.DataFrame({
            'Team': df['Team'].unique(),
            'Matches': 0,
            'Wins': 0,
            'Losses': 0,
            'NRR': 0.00,
            'Points': 0,
            'Qualified': '',
            'Form': ''  # Add a column for form (arrows)
        })
    if 'playoffs_results' not in st.session_state:
        st.session_state.playoffs_results = None
    if 'playoffs_step' not in st.session_state:
        st.session_state.playoffs_step = 0
    if 'recent_teams' not in st.session_state:
        st.session_state.recent_teams = []  # Track recently played teams
    if 'team_form' not in st.session_state:
        st.session_state.team_form = {team: [] for team in df['Team'].unique()}  # Track form for each team

    # Display Team Balance Report
    st.subheader("Team Balance Report")
    st.write(st.session_state.balance_report)

    teams = st.session_state.balance_report.index.tolist()
    ratings = st.session_state.balance_report['Average Rating'].to_dict()
    fixtures = generate_fixtures(teams)
    start_date = datetime(2024, 3, 22)  # Start date for the tournament
    schedule_df = generate_schedule(fixtures, start_date)

    # Display Next Match
    if len(st.session_state.results) < len(fixtures):
        next_match_index = len(st.session_state.results)
        next_match = fixtures[next_match_index]
        st.subheader("Next Match")
        st.markdown(f"**Match No. {next_match_index + 1}: {next_match}**")  # Add match number

    # Display Match Results
    st.subheader("Match Results")
    results_df = pd.DataFrame(st.session_state.results)
    results_df.index = range(1, len(results_df) + 1)  # Start numbering from 1
    st.write(results_df.sort_index(ascending=False))

    # Points Calculation Explanation
    st.markdown("""
    **Points Calculation:**
    - Each win awards 2 points.
    - No points are awarded for a loss.
    - Net Run Rate (NRR) is adjusted randomly for each match.
    """)

    # Team Balance Metrics Explanation
    st.markdown("""
    **Team Balance Metrics:**
    - **Total Players:** Total number of players in the squad.
    - **Foreign Players:** Number of players who are not Indian.
    - **Batters:** Number of players with the role 'Batter'.
    - **Wicketkeepers:** Number of players with the role 'Wicketkeeper'.
    - **Allrounders:** Number of players with the role 'Allrounder'.
    - **Bowlers:** Number of players with the role 'Bowler'.
    - **Average Rating:** Average rating of all players in the squad.
    - **Balanced:** Indicates if the team meets the balance criteria.
    """)

    # Team Balance Metrics Explanation
    st.markdown("""
    **Balance Team Criteria:**
    - **Total Players:** 11
    - **Foreign Players:** Not More Than 4.
    - **Batters:** 4 (Can Play W/K as Batsman)
    - **Wicketkeepers:** 1
    - **Allrounders:** 2 or 3
    - **Bowlers:** 4 or 3
    - **Note:** If 2 Allrounders then, 4 Bowlers or If 3 Allrounders then, 3 Bowlers 
    """)

    # Check if all matches are completed
    if len(st.session_state.results) == len(fixtures):
        top_4 = st.session_state.points_table.sort_values(by=['Points', 'NRR'], ascending=[False, False]).head(4)
        top_4.index = range(1, len(top_4) + 1)  # Start numbering from 1

        # Mark top 4 teams as qualified
        st.session_state.points_table['Qualified'] = ''  # Reset qualification status
        for i in range(4):
            st.session_state.points_table.loc[st.session_state.points_table['Team'] == top_4.iloc[i]['Team'], 'Qualified'] = 'Q'

        # Simulate playoffs step-by-step
        if st.session_state.playoffs_results is None:
            st.session_state.playoffs_results = {
                "q1_winner": None,
                "q1_loser": None,
                "eliminator_winner": None,
                "qualifier2_winner": None,
                "final_winner": None,
                "final_loser": None,
                "first": None,
                "second": None,
                "third": None
            }

        if st.session_state.playoffs_step == 0:
            if st.sidebar.button("Simulate Next Playoff Match"):
                q1_winner = simulate_match(top_4.iloc[0]['Team'], top_4.iloc[1]['Team'], ratings, st.session_state.balance_report)
                q1_loser = top_4.iloc[0]['Team'] if q1_winner == top_4.iloc[1]['Team'] else top_4.iloc[1]['Team']
                st.session_state.playoffs_results["q1_winner"] = q1_winner
                st.session_state.playoffs_results["q1_loser"] = q1_loser
                st.session_state.playoffs_step += 1

        elif st.session_state.playoffs_step == 1:
            if st.sidebar.button("Simulate Next Playoff Match"):
                eliminator_winner = simulate_match(top_4.iloc[2]['Team'], top_4.iloc[3]['Team'], ratings, st.session_state.balance_report)
                st.session_state.playoffs_results["eliminator_winner"] = eliminator_winner
                st.session_state.playoffs_step += 1

        elif st.session_state.playoffs_step == 2:
            if st.sidebar.button("Simulate Next Playoff Match"):
                qualifier2_winner = simulate_match(st.session_state.playoffs_results["q1_loser"], st.session_state.playoffs_results["eliminator_winner"], ratings, st.session_state.balance_report)
                qualifier2_loser = st.session_state.playoffs_results["q1_loser"] if qualifier2_winner == st.session_state.playoffs_results["eliminator_winner"] else st.session_state.playoffs_results["eliminator_winner"]
                st.session_state.playoffs_results["qualifier2_winner"] = qualifier2_winner
                st.session_state.playoffs_results["qualifier2_loser"] = qualifier2_loser
                st.session_state.playoffs_step += 1

        elif st.session_state.playoffs_step == 3:
            if st.sidebar.button("Simulate Next Playoff Match"):
                final_winner = simulate_match(st.session_state.playoffs_results["q1_winner"], st.session_state.playoffs_results["qualifier2_winner"], ratings, st.session_state.balance_report)
                final_loser = st.session_state.playoffs_results["q1_winner"] if final_winner == st.session_state.playoffs_results["qualifier2_winner"] else st.session_state.playoffs_results["qualifier2_winner"]
                st.session_state.playoffs_results["final_winner"] = final_winner
                st.session_state.playoffs_results["final_loser"] = final_loser
                st.session_state.playoffs_results["first"] = final_winner
                st.session_state.playoffs_results["second"] = final_loser
                st.session_state.playoffs_results["third"] = st.session_state.playoffs_results["qualifier2_loser"]
                st.session_state.playoffs_step += 1

        # Display playoffs results in the sidebar
        st.sidebar.header("Playoffs Results")
        st.sidebar.markdown(f"**Qualifier 1:** {top_4.iloc[0]['Team']} vs {top_4.iloc[1]['Team']} → **Winner:** {st.session_state.playoffs_results['q1_winner']}")
        st.sidebar.markdown(f"**Eliminator:** {top_4.iloc[2]['Team']} vs {top_4.iloc[3]['Team']} → **Winner:** {st.session_state.playoffs_results['eliminator_winner']}")
        st.sidebar.markdown(f"**Qualifier 2:** {st.session_state.playoffs_results['q1_loser']} vs {st.session_state.playoffs_results['eliminator_winner']} → **Winner:** {st.session_state.playoffs_results['qualifier2_winner']}")
        st.sidebar.markdown(f"**🏆 Final:** {st.session_state.playoffs_results['q1_winner']} vs {st.session_state.playoffs_results['qualifier2_winner']} → **Champion:** {st.session_state.playoffs_results['final_winner']}")
        st.sidebar.markdown(f"**First Place:** {st.session_state.playoffs_results['first']}")
        st.sidebar.markdown(f"**Second Place:** {st.session_state.playoffs_results['second']}")
        st.sidebar.markdown(f"**Third Place:** {st.session_state.playoffs_results['third']}")

    # Display points table on the side
    st.sidebar.header("Points Table")

    # Add arrows for wins and losses based on recent form
    points_table_display = st.session_state.points_table.sort_values(by=['Points', 'NRR'], ascending=[False, False])
    points_table_display.index = range(1, len(points_table_display) + 1)  # Start numbering from 1

    # Update form based on recent results
    for team in points_table_display['Team']:
        if st.session_state.team_form[team]:
            latest_result = st.session_state.team_form[team][-1]  # Get the latest result
            if latest_result == 'W':
                points_table_display.loc[points_table_display['Team'] == team, 'Form'] = f"<span style='color: green;'>↑</span>"
            elif latest_result == 'L':
                points_table_display.loc[points_table_display['Team'] == team, 'Form'] = f"<span style='color: red;'>↓</span>"

    # Custom CSS for smaller and flexible table
    st.sidebar.markdown(
        """
        <style>
        .small-table {
            font-size: 12px;
            width: 100%;
            margin: 0;
            padding: 0;
        }
        .small-table th, .small-table td {
            padding: 4px;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display the points table with HTML formatting
    st.sidebar.markdown(
        points_table_display.to_html(classes='small-table', escape=False, index=False),
        unsafe_allow_html=True
    )

    # Play next match on button click
    if len(st.session_state.results) < len(fixtures):
        if st.sidebar.button("Play Next Match"):
            current_match = fixtures[len(st.session_state.results)]
            team1, team2 = current_match.split(' vs ')
            winner = simulate_match(team1, team2, ratings, st.session_state.balance_report)
            loser = team1 if winner == team2 else team2

            # Update results
            st.session_state.results.append({'Match': current_match, 'Winner': winner})

            # Update points table
            st.session_state.points_table.loc[st.session_state.points_table['Team'] == winner, 'Wins'] += 1
            st.session_state.points_table.loc[st.session_state.points_table['Team'] == winner, 'Points'] += 2
            st.session_state.points_table.loc[st.session_state.points_table['Team'] == winner, 'Matches'] += 1

            st.session_state.points_table.loc[st.session_state.points_table['Team'] == loser, 'Losses'] += 1
            st.session_state.points_table.loc[st.session_state.points_table['Team'] == loser, 'Matches'] += 1

            # Update team form
            st.session_state.team_form[winner].append('W')  # Add win to winner's form
            st.session_state.team_form[loser].append('L')  # Add loss to loser's form

            # Randomly tweak NRR for drama
            st.session_state.points_table.loc[st.session_state.points_table['Team'] == winner, 'NRR'] += round(random.uniform(0.01, 0.10), 2)
            st.session_state.points_table.loc[st.session_state.points_table['Team'] == loser, 'NRR'] -= round(random.uniform(0.01, 0.10), 2)