document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('#course_exists').addEventListener('change', function () {
        document.querySelector('#new_course_name').style.display = "none";
        document.querySelector('#new_tees').style.display = "none";
    })
})