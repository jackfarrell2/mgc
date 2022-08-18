document.addEventListener('DOMContentLoaded', function () {
    // Clear tee option when new course is selected
    document.querySelector('#new-course-or-tees-course').addEventListener('click', function () {
        document.querySelector('#already_course').style.display = "none";
        document.querySelector('#new_course').style.display = "none";
        document.querySelector('#tees').value = 'Tees';
        document.querySelector('#course_exists').value = 'Course';
        document.querySelector('#new_course').style.display = "block";
        document.querySelector('#course-or-tees').value = "Course";
        return false;
    })

    // Clear new course option when new tee is selected
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

// Check user input
function validateMyForm() {
    let already_course = document.querySelector('#already_course');
    let new_course = document.querySelector('#new_course');
    // Check if the user selected new course or new tees
    if (already_course.style.display === 'none' && new_course.style.display === 'none') {
        alert("Please choose if you are adding an entirely new course or just new tees");
        return false;
    } 
    // Check if user selected entirely new course
    else if (already_course.style.display === 'none') {
        let tees = document.querySelector('#new_tees');
        let course_name = document.querySelector('#new_course_name');
        // Check if user selected a valid tee option
        if (tees.value === 'Tees') {
            alert("Please select an option for the tees.");
            return false;
        } 
        // Check if user entered a valid course name
        if (course_name.value === '') {
            alert("Please enter a course name.");
            return false;
        } 
    } 
    // Check if user selected a new tee option
    else if (new_course.style.display === 'none') {
        let tees = document.querySelector('#tees');
        let course_name = document.querySelector('#course_exists');
        // Check if user selected a valid tee option
        if (tees.value === 'Tees') {
            alert("Please select an option for the tees.");
            return false;
        } 
        // Check if user selected a valid course name
        if (course_name.value === 'Course') {
            alert("Please select an option for the course name.");
            return false;
        }
    }

    // Check if all the numbers on the scorecard add up
    let yardage_row = document.getElementsByClassName('yardages-row')[0];
    let par_row = document.getElementsByClassName('pars-row')[0];
    let handicap_row = document.getElementsByClassName('handicap-row')[0];
    let yardages = [];
    let pars = [];
    let handicaps = [];
    // Populate yardages, pars, and handicaps the user entered
    for (let i = 0; i < yardage_row.childElementCount; i++) {
        // Only on the rows of the scorecard that matter
        if (i != 0 && i != 10 && i != 20 && i != 21) {
            yardages.push(yardage_row.children[i].children[0].value);
            pars.push(par_row.children[i].children[0].value);
            handicaps.push(handicap_row.children[i].children[0].value);
        }
    }
    // Check the users math
    let front_nine_sum_yardages = 0;
    let back_nine_sum_yardages = 0;
    let total_sum_yardages = 0;
    let front_nine_sum_pars = 0;
    let back_nine_sum_pars = 0;
    let total_sum_pars = 0;
    for (let i = 0; i < 18; i++) {
        if (i < 9) {
            front_nine_sum_yardages += parseInt(yardages[i]);
            total_sum_yardages += parseInt(yardages[i]);
            front_nine_sum_pars += parseInt(pars[i]);
            total_sum_pars += parseInt(pars[i]);
        }
        else {
            back_nine_sum_yardages += parseInt(yardages[i]);
            total_sum_yardages += parseInt(yardages[i]);
            back_nine_sum_pars += parseInt(pars[i]);
            total_sum_pars += parseInt(pars[i]);
        }
    }
    let front_nine_yardage_given = yardage_row.children[10].children[0].value;
    let back_nine_yardage_given = yardage_row.children[20].children[0].value;
    let total_yardage_given = yardage_row.children[21].children[0].value;
    let front_nine_par_given = par_row.children[10].children[0].value;
    let back_nine_par_given = par_row.children[20].children[0].value;
    let total_par_given = par_row.children[21].children[0].value;

    // Front nine yardage does not add up
    if (front_nine_sum_yardages != front_nine_yardage_given) {
        alert("The front nine yardages do not add up to the front nine yardage total.");
        return false;
    } 
    // Back nine yardage does not add up
    else if (back_nine_sum_yardages != back_nine_yardage_given) {
        alert("The back nine yardages do not add up to the back nine yardage total.");
        return false;
    } 
    // Total yardage does not add up
    else if (total_sum_yardages != total_yardage_given) {
        alert("The yardages by hole do not add up to the yardage total.");
        return false;
    } 
    // Front nine pars do not add up
    else if (front_nine_sum_pars != front_nine_par_given) {
        alert("The front nine pars do not add up to the front nine par total.");
        return false;
    } 
    // Back nine pars do not add up
    else if (back_nine_sum_pars != back_nine_par_given) {
        alert("The back nine pars do not add up to the back nine par total.");
        return false;
    } 
    // Total pars do not add up
    else if (total_sum_pars != total_par_given) {
        alert("The pars by hole do not add up to the par total.");
        return false;
    } 
    // Check handicap row does not have duplicates
    let handicap_set = new Set(handicaps);
    if (handicap_set.size != handicaps.length) {
        alert("Each hole must have a unique handicap.");
        return false;
    }
    // Check user inputted valid slope and course rating
    let slope = parseInt(document.querySelector('#slope').value);
    let rating = document.querySelector('#rating').value;
    if (isNaN(slope)) {
        alert("Invalid Slope Rating");
        return false;
    } else {
        if (slope < 55 || slope > 155) {
            alert("Invalid Slope Rating");
            return false;
        }
    }
    if (isNaN(rating)) {
        alert("Invalid Course Rating");
        return false;
    } else {
        if (rating < 60 || rating > 81 || rating.toString().length != 4) {
            alert("Invalid Course Rating");
            return false;
        }
    }
}