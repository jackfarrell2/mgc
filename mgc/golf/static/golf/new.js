document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('#new-course-or-tees-course').addEventListener('click', function () {
        document.querySelector('#already_course').style.display = "none";
        document.querySelector('#new_course').style.display = "none";
        document.querySelector('#tees').value = 'Tees';
        document.querySelector('#course_exists').value = 'Course';
        document.querySelector('#new_course').style.display = "block";
        document.querySelector('#course-or-tees').value = "Course";
        return false;
    })

    document.querySelector('#new-course-or-tees-tees').addEventListener('click', function () {
        document.querySelector('#already_course').style.display = "none";
        document.querySelector('#new_course').style.display = "none";
        document.querySelector('#new_tees').value = 'Tees';
        document.querySelector('#new_course_name').value = '';
        document.querySelector('#already_course').style.display = "block";
        document.querySelector('#course-or-tees').value = "Tees";
        return false;
    })
})

function validateMyForm() {
    let already_course = document.querySelector('#already_course');
    let new_course = document.querySelector('#new_course');
    if (already_course.style.display === 'none' && new_course.style.display === 'none') {
        alert("Please choose if you are adding an entirely new course or just new tees");
        return false;
    }
    if (already_course.style.display === 'none' && new_course.style.display === 'none') {
        alert("Please choose if you are adding an entirely new course or just new tees");
        return false;
    } else if (already_course.style.display === 'none') {
        let tees = document.querySelector('#new_tees');
        let course_name = document.querySelector('#new_course_name');
        if (tees.value === 'Tees') {
            alert("Please select an option for the tees.");
            return false;
        } else if (course_name.value === '') {
            alert("Please enter a course name.");
            return false;
        } else {
            return true;
        }
    } else if (new_course.style.display === 'none') {
        let tees = document.querySelector('#tees');
        let course_name = document.querySelector('#course_exists');
        if (tees.value === 'Tees') {
            alert("Please select an option for the tees.");
            return false;
        } else if (course_name.value === 'Course') {
            alert("Please select an option for the course name.");
            return false;
        } else {
            return true;
        }

    }
}