# ml/run_odds_pipeline.py
import joblib
from ml.edge_engine import evaluate_matches
from ml.feature_builder import build_features
from ml.mock_odds import ingest_mock
from sqlalchemy import text
from app.database import engine

MODEL_PATH = "/data/ml/tennis_model_calibrated.joblib"
FEATURES = ["elo_diff"]
MODEL_NAME = "elo"
MODEL_VERSION = "v1_calibrated"

model = joblib.load(MODEL_PATH)

def persist_value_bets(df):
    if df.empty:
        return

    rows = []
    for _, r in df.iterrows():
        side = "A" if r.bet_a else "B"

        rows.append({
            "provider": "mock",
            "bookmaker": "mockbook",
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,

            "min_edge_rule": 0.08,

            "event_id": r.event_id,
            "commence_time": r.commence_time,

            "player_a_id": r.player_a_id,
            "player_a_name": r.player_a,

            "player_b_id": r.player_b_id,
            "player_b_name": r.player_b,

            "side": side,  

            "prob_a": r.prob_a,
            "prob_b": r.prob_b,

            "odds_a": r.odds_player_a,
            "odds_b": r.odds_player_b,

            "edge_a": r.edge_a,
            "edge_b": r.edge_b,
        })


    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO value_bets (
                    provider,
                    bookmaker,
                    model_name,
                    model_version,  
                    min_edge_rule,
                    event_id,
                    commence_time,

                    player_a_id,
                    player_a_name,

                    player_b_id,
                    player_b_name,

                    side,

                    prob_a,
                    prob_b,
                    odds_a,
                    odds_b,
                    edge_a,
                    edge_b
                )
                VALUES (
                    :provider,
                    :bookmaker,
                    :model_name,
                    :model_version,
                    :min_edge_rule,
                    :event_id,
                    :commence_time,

                    :player_a_id,
                    :player_a_name,

                    :player_b_id,
                    :player_b_name,

                    :side,

                    :prob_a,
                    :prob_b,
                    :odds_a,
                    :odds_b,
                    :edge_a,
                    :edge_b
                )
                ON CONFLICT DO NOTHING
            """),
            rows
        )

def main():
    print("▶️ Avvio pipeline odds (MOCK MODE)")

    odds_df = ingest_mock()
    if odds_df.empty:
        print("⚠️ Nessuna odds disponibile")
        return

    features_df = build_features(odds_df)

    X = features_df[FEATURES]
    probs = model.predict_proba(X)

    features_df["prob_a"] = probs[:, 1]
    features_df["prob_b"] = probs[:, 0]

    evaluated = evaluate_matches(features_df)

    # TEMP: force mock value bet for frontend testing
    if evaluated.empty:
        print("⚠️ No evaluated matches")
        return

    evaluated.loc[evaluated.index[0], "edge_a"] = 0.08
    evaluated.loc[evaluated.index[0], "bet_a"] = True

    value_bets = evaluated[
        evaluated.bet_a | evaluated.bet_b
    ].copy()

    print(f"🎯 Value bets trovate: {len(value_bets)}")
    print(value_bets.columns.tolist())
    persist_value_bets(value_bets)

    # LOG (il DB lo collegheremo dopo)
    for _, r in value_bets.iterrows():
        side = "A" if r.bet_a else "B"
        edge = r.edge_a if r.bet_a else r.edge_b
        print(
            f"✅ {r.player_a} vs {r.player_b} | side={side} | edge={edge:.3f}"
        )


if __name__ == "__main__":
    main()
