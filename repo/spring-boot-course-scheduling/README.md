# Teaching Affairs Course Scheduling System

## Project Description
This project is a backend system for a university course scheduling system. It manages basic data (terms, classrooms, teachers, courses) and handles the scheduling of course offerings into classrooms and time slots.

## Functional Requirements
1.  **Basic Data Management**: Manage Terms, Classrooms, Departments, Majors, Teachers.
2.  **Course Management**: Manage Courses and Course Offerings (a course offered in a specific term for specific majors).
3.  **Scheduling**:
    -   Define time slots (e.g., Mon 1-2, Mon 3-4).
    -   Auto-schedule course offerings into classrooms and time slots avoiding conflicts.
    -   Manual adjustment of schedules.
    -   View schedules by teacher, classroom, or student group.

## API Definitions
The service should listen on port `8080` (default). All APIs are prefixed with `/api`.

### 1. Term Management
-   `POST /api/terms`: Create a new term.
    -   Input: `{ "name": "2024-Fall", "startDate": "2024-09-01", "endDate": "2025-01-15" }`
    -   Output: `{ "id": 1, "name": "2024-Fall", ... }`
-   `GET /api/terms`: List all terms.
-   `GET /api/terms/{id}`: Get term details.
-   `PUT /api/terms/{id}`: Update term.
-   `DELETE /api/terms/{id}`: Delete term.

### 2. Classroom Management
-   `POST /api/classrooms`: Create a classroom.
    -   Input: `{ "name": "Building A 101", "capacity": 50, "type": "MULTIMEDIA" }`
    -   Output: `{ "id": 1, ... }`
-   `GET /api/classrooms`: List classrooms.
-   `GET /api/classrooms/{id}`: Get classroom details.
-   `PUT /api/classrooms/{id}`: Update classroom.
-   `DELETE /api/classrooms/{id}`: Delete classroom.

### 3. Department Management
-   `POST /api/departments`: Create a department.
    -   Input: `{ "name": "Computer Science" }`
    -   Output: `{ "id": 1, ... }`
-   `GET /api/departments`: List departments.
-   `DELETE /api/departments/{id}`: Delete department.

### 4. Teacher Management
-   `POST /api/teachers`: Create a teacher.
    -   Input: `{ "name": "John Doe", "departmentId": 1 }`
    -   Output: `{ "id": 1, ... }`
-   `GET /api/teachers`: List teachers.
-   `GET /api/teachers/{id}`: Get teacher details.
-   `PUT /api/teachers/{id}`: Update teacher.
-   `DELETE /api/teachers/{id}`: Delete teacher.

### 5. Course Management
-   `POST /api/courses`: Create a course.
    -   Input: `{ "name": "Intro to Java", "credits": 3, "departmentId": 1 }`
    -   Output: `{ "id": 1, ... }`
-   `GET /api/courses`: List courses.
-   `GET /api/courses/{id}`: Get course details.
-   `PUT /api/courses/{id}`: Update course.
-   `DELETE /api/courses/{id}`: Delete course.

### 6. Course Offering Management
-   `POST /api/offerings`: Create a course offering.
    -   Input: `{ "courseId": 1, "termId": 1, "teacherId": 1, "maxCapacity": 50 }`
    -   Output: `{ "id": 1, ... }`
-   `GET /api/offerings`: List offerings.
-   `GET /api/offerings/{id}`: Get offering details.

### 7. Scheduling Constraints
-   `POST /api/constraints`: Add a constraint (e.g., Teacher X cannot teach on Fri afternoon).
    -   Input: `{ "teacherId": 1, "dayOfWeek": 5, "period": 3, "type": "UNAVAILABLE" }`
    -   Output: `{ "id": 1, ... }`
-   `GET /api/constraints`: List constraints.

### 8. Schedule Management
-   `POST /api/schedule/auto`: Trigger auto-scheduling for a term.
    -   Input: `{ "termId": 1 }`
    -   Output: `{ "status": "SUCCESS", "scheduledCount": 10, "failedCount": 0 }`
-   `GET /api/schedule/term/{termId}`: Get full schedule for a term.
-   `POST /api/schedule/manual`: Manually assign/move a class.
    -   Input: `{ "offeringId": 1, "classroomId": 1, "dayOfWeek": 1, "period": 1 }`
    -   Output: `{ "success": true }`
-   `GET /api/schedule/teacher/{teacherId}`: Get schedule for a teacher.
-   `GET /api/schedule/classroom/{classroomId}`: Get schedule for a classroom.

## Metrics
-   **Test Case Pass Rate**: 100% (All provided tests must pass).
-   **Repo Pass Rate**: 100% (The implementation must be complete).

## Testing
Run the tests using `mvn test`. The tests are located in `tests/` and use RestAssured to verify the API implementation.
