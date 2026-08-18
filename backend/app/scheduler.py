"""
GeoFace Faculty Authentication System - Background Scheduler
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date
import logging

from .extensions import db
from .models.teacher import Teacher
from .models.attendance import AttendanceLog

logger = logging.getLogger(__name__)

def mark_absent_teachers(app):
    """
    Scans all active teachers at the end of the day.
    If a teacher has no successful check-in or half-day for today, marks them absent.
    """
    with app.app_context():
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        logger.info(f"Running automated absent marking for {today}...")

        # 1. Check if today is a weekend (Saturday=5, Sunday=6)
        if today.weekday() >= 5:
            logger.info("Today is a weekend. Skipping auto-absent marking.")
            return

        # 2. Check if today is a public holiday
        from .models.holiday import Holiday
        if Holiday.query.filter_by(date=today, is_full_day=True).first():
            logger.info("Today is a public holiday. Skipping auto-absent marking.")
            return
        
        # Get all active teachers
        active_teachers = Teacher.query.filter_by(is_active=True).all()
        marked_count = 0
        
        from .models.leave import LeaveRequest
        
        for teacher in active_teachers:
            # Check if teacher is on approved leave today
            on_leave = LeaveRequest.query.filter(
                LeaveRequest.teacher_id == teacher.teacher_id,
                LeaveRequest.status == 'approved',
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today
            ).first()
            
            if on_leave:
                # Skip auto-absent if they have an approved leave
                continue
                
            # Check if teacher has any successful log today
            has_attendance = AttendanceLog.query.filter(
                AttendanceLog.teacher_id == teacher.teacher_id,
                AttendanceLog.timestamp >= today_start,
                AttendanceLog.timestamp <= today_end,
                AttendanceLog.status == "success",
                AttendanceLog.attendance_mark.in_(["present", "half_day", "flagged"])
            ).first()
            
            if not has_attendance:
                # Create an absent log
                absent_log = AttendanceLog(
                    teacher_id=teacher.teacher_id,
                    action_type="check_in",
                    status="failure",
                    reason="Absent (System Auto-Mark)",
                    attendance_mark="absent",
                    timestamp=datetime.utcnow()
                )
                db.session.add(absent_log)
                marked_count += 1
                
        db.session.commit()
        logger.info(f"Auto-marked {marked_count} teachers as absent.")

def init_scheduler(app):
    """Initialize and start the background scheduler."""
    scheduler = BackgroundScheduler(daemon=True)
    
    # Schedule the job to run every day at 17:00 (5:00 PM) server time
    scheduler.add_job(
        func=mark_absent_teachers,
        args=[app],
        trigger=CronTrigger(hour=17, minute=0),
        id="auto_absent_marker",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("APScheduler initialized. Auto-absent marker scheduled for 17:00 daily.")
    return scheduler
