"""
Analytics Router — Dashboard stats and progress tracking.
"""
import logging
from fastapi import APIRouter, Depends
from services import db
from services.auth_utils import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard(user_id: str = Depends(get_current_user_id)):
    """Get dashboard summary statistics."""
    return db.get_dashboard_stats(user_id)


@router.get("/progress")
async def get_progress(user_id: str = Depends(get_current_user_id)):
    """Get trainee progress data for charts."""
    return db.get_progress_data(user_id)


@router.get("/leaderboard")
async def get_leaderboard(user_id: str = Depends(get_current_user_id)):
    """Get comparative performance leaderboard."""
    conn = db.get_connection()

    # Get top performers by average overall score
    rows = conn.execute("""
        SELECT u.id, u.full_name, u.email,
               COUNT(e.id) as total_evaluations,
               COALESCE(AVG(e.overall_score), 0) as avg_score,
               COALESCE(MAX(e.overall_score), 0) as best_score
        FROM users u
        LEFT JOIN evaluations e ON u.id = e.user_id
        GROUP BY u.id
        HAVING total_evaluations > 0
        ORDER BY avg_score DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    leaderboard = []
    for i, r in enumerate(rows):
        d = dict(r)
        d["rank"] = i + 1
        d["avg_score"] = round(d["avg_score"], 1)
        d["best_score"] = round(d["best_score"], 1)
        # Anonymize email for privacy
        email = d.pop("email", "")
        d["display_name"] = d.get("full_name") or email.split("@")[0]
        d["is_current_user"] = d["id"] == user_id
        leaderboard.append(d)

    return leaderboard
