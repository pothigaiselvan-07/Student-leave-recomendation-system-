import streamlit as st
import pandas as pd
from datetime import datetime
from enum import Enum

# Page configuration
st.set_page_config(
    page_title="Student Leave Recommendation",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

class LeaveType(Enum):
    MEDICAL = "Medical"
    PERSONAL = "Personal"
    EMERGENCY = "Emergency"
    CASUAL = "Casual"
    ACADEMIC = "Academic Activity"

class AttendanceLevel(Enum):
    EXCELLENT = "Excellent (>90%)"
    GOOD = "Good (75-90%)"
    AVERAGE = "Average (60-75%)"
    POOR = "Poor (<60%)"

def evaluate_leave_request(student_data):
    """
    Rule-based logic to evaluate leave requests
    Returns: (recommendation, score, reasoning)
    """
    
    recommendation = "APPROVED"
    score = 100
    reasons = []
    
    # Rule 1: Check leave balance
    if student_data['leave_balance'] < student_data['days_requested']:
        recommendation = "REJECTED"
        score -= 50
        reasons.append(f"❌ Insufficient leave balance. Requested: {student_data['days_requested']} days, Available: {student_data['leave_balance']} days")
    else:
        reasons.append(f"✅ Sufficient leave balance ({student_data['leave_balance']} days available)")
    
    # Rule 2: Check leave type and attendance
    if student_data['attendance'] == "Poor (<60%)":
        if student_data['leave_type'] in ["Casual", "Personal"]:
            recommendation = "REJECTED"
            score -= 40
            reasons.append("❌ Poor attendance. Casual/Personal leaves not recommended")
        else:
            score -= 20
            reasons.append("⚠️ Poor attendance, but leave type qualifies for approval")
    else:
        reasons.append(f"✅ Acceptable attendance level ({student_data['attendance']})")
    
    # Rule 3: Check if exam period
    if student_data['exam_period']:
        if student_data['leave_type'] == "Casual":
            recommendation = "PENDING"
            score -= 30
            reasons.append("⚠️ Leave requested during exam period - requires principal approval")
        elif student_data['leave_type'] == "Emergency":
            reasons.append("✅ Emergency leave during exam period can be approved")
        elif student_data['leave_type'] == "Medical":
            reasons.append("✅ Medical leave during exam period acceptable")
    else:
        reasons.append("✅ Leave requested outside exam period")
    
    # Rule 4: Check days requested
    if student_data['days_requested'] > 7:
        if student_data['attendance'] in ["Good (75-90%)", "Excellent (>90%)"]:
            score -= 10
            reasons.append("⚠️ Long leave duration (>7 days) - requires documentation")
        else:
            recommendation = "PENDING"
            score -= 25
            reasons.append("⚠️ Long leave duration with moderate attendance - needs approval")
    else:
        reasons.append(f"✅ Reasonable leave duration ({student_data['days_requested']} days)")
    
    # Rule 5: Leave type specific rules
    if student_data['leave_type'] == "Medical":
        reasons.append("✅ Medical leave - high priority")
        score = min(100, score + 10)
    elif student_data['leave_type'] == "Emergency":
        reasons.append("✅ Emergency leave - approved with documentation")
        score = min(100, score + 10)
    elif student_data['leave_type'] == "Academic Activity":
        reasons.append("✅ Academic activity leave - encouraged")
        score = min(100, score + 15)
    
    # Rule 6: Previous leave pattern
    if student_data['leaves_taken'] > 12:
        score -= 15
        reasons.append(f"⚠️ High number of leaves already taken this year ({student_data['leaves_taken']})")
    else:
        reasons.append(f"✅ Reasonable leave pattern ({student_data['leaves_taken']} leaves taken so far)")
    
    # Ensure score is between 0-100
    score = max(0, min(100, score))
    
    # Final decision based on score
    if score < 30:
        recommendation = "REJECTED"
    elif score < 60:
        recommendation = "PENDING"
    elif recommendation == "REJECTED":
        recommendation = "PENDING"
    
    return recommendation, score, reasons

# Main app
st.title("📚 Student Leave Recommendation System")
st.markdown("*AI-powered system to help evaluate and recommend student leave requests*")

# Sidebar for instructions
with st.sidebar:
    st.header("📖 Instructions")
    st.info("""
    1. Fill in student details
    2. Enter leave request information
    3. Get recommendation with detailed reasoning
    4. Share with authorities
    """)
    
    st.markdown("---")
    st.subheader("📊 Quick Stats")
    st.caption("This system uses rule-based logic to ensure fair evaluation")

# Main form
col1, col2 = st.columns(2)

with col1:
    st.subheader("👤 Student Information")
    
    student_id = st.text_input("Student ID", placeholder="e.g., STU001")
    student_name = st.text_input("Student Name", placeholder="Enter full name")
    semester = st.selectbox("Semester", ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"])
    department = st.text_input("Department", placeholder="e.g., Computer Science")

with col2:
    st.subheader("📋 Academic Details")
    
    attendance = st.selectbox(
        "Current Attendance",
        [enum.value for enum in AttendanceLevel]
    )
    
    leaves_taken = st.number_input(
        "Leaves Already Taken This Year",
        min_value=0,
        max_value=50,
        value=5
    )
    
    leave_balance = st.number_input(
        "Remaining Leave Balance",
        min_value=0,
        max_value=60,
        value=20
    )

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.subheader("📅 Leave Request Details")
    
    leave_type = st.selectbox(
        "Type of Leave",
        [enum.value for enum in LeaveType]
    )
    
    days_requested = st.number_input(
        "Number of Days Requested",
        min_value=1,
        max_value=30,
        value=3
    )
    
    leave_from = st.date_input("Leave From Date")

with col4:
    st.subheader("📌 Additional Information")
    
    leave_to = st.date_input("Leave To Date")
    
    exam_period = st.checkbox("Leave during exam period?")
    
    reason = st.text_area(
        "Reason for Leave (optional)",
        placeholder="Provide additional context if needed",
        height=100
    )

# Process button
st.markdown("---")

if st.button("🔍 Get Recommendation", use_container_width=True, type="primary"):
    
    # Validate inputs
    if not student_id or not student_name:
        st.error("❌ Please fill in Student ID and Name")
    elif leave_from > leave_to:
        st.error("❌ Leave From date must be before Leave To date")
    else:
        # Prepare data for evaluation
        student_data = {
            'leave_balance': leave_balance,
            'days_requested': days_requested,
            'attendance': attendance,
            'leave_type': leave_type,
            'exam_period': exam_period,
            'leaves_taken': leaves_taken
        }
        
        # Get recommendation
        recommendation, score, reasons = evaluate_leave_request(student_data)
        
        # Display results
        st.success("✅ Evaluation Complete!")
        
        st.markdown("---")
        
        # Recommendation box
        col5, col6, col7 = st.columns(3)
        
        with col5:
            if recommendation == "APPROVED":
                st.metric("Recommendation", "✅ APPROVED", "Ready to Submit")
            elif recommendation == "PENDING":
                st.metric("Recommendation", "⏳ PENDING", "Needs Approval")
            else:
                st.metric("Recommendation", "❌ REJECTED", "Not Recommended")
        
        with col6:
            st.metric("Confidence Score", f"{score}%", f"{score} out of 100")
        
        with col7:
            st.metric("Days Remaining", f"{leave_balance - days_requested}", "After leave")
        
        st.markdown("---")
        
        # Detailed reasoning
        st.subheader("📝 Detailed Analysis")
        
        col8, col9 = st.columns([1, 2])
        
        with col8:
            st.subheader("Request Summary")
            st.info(f"""
            **Student:** {student_name} ({student_id})
            
            **Department:** {department}
            
            **Semester:** {semester}
            
            **Leave Type:** {leave_type}
            
            **Duration:** {days_requested} days ({leave_from} to {leave_to})
            """)
        
        with col9:
            st.subheader("Evaluation Reasoning")
            for reason_text in reasons:
                st.write(reason_text)
        
        # Additional notes
        if recommendation == "PENDING":
            st.warning("""
            ⚠️ **This leave requires additional approval from:**
            - Department Head
            - Principal/Dean
            
            Please attach supporting documents if necessary.
            """)
        elif recommendation == "REJECTED":
            st.error("""
            ❌ **This leave cannot be approved because:**
            
            Based on the current policy and your attendance/leave balance,
            this request does not meet approval criteria.
            
            **Suggestion:** Consult with your class advisor for alternatives.
            """)
        else:
            st.success("""
            ✅ **Your leave request is approved!**
            
            You can now submit this recommendation to your department.
            Keep a copy for your records.
            """)
        
        # Export button
        st.markdown("---")
        
        # Create summary for download
        summary = f"""
STUDENT LEAVE RECOMMENDATION REPORT
===================================

Student Details:
- Name: {student_name}
- ID: {student_id}
- Department: {department}
- Semester: {semester}

Leave Request:
- Type: {leave_type}
- From: {leave_from}
- To: {leave_to}
- Duration: {days_requested} days
- Reason: {reason if reason else "Not provided"}

Academic Information:
- Attendance: {attendance}
- Leaves Taken This Year: {leaves_taken}
- Leave Balance: {leave_balance}
- During Exam Period: {"Yes" if exam_period else "No"}

Recommendation: {recommendation}
Confidence Score: {score}%

Reasoning:
{chr(10).join(reasons)}

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        st.download_button(
            label="📥 Download Recommendation Report",
            data=summary,
            file_name=f"leave_recommendation_{student_id}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
<p>Student Leave Recommendation System v1.0 | Built with Streamlit</p>
<p>For support or issues, contact your IT Department</p>
</div>
""", unsafe_allow_html=True)
