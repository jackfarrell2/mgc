document.addEventListener('DOMContentLoaded', function () {
    // Clear tee option when new course is selected
    document.querySelector('#new-course-or-tees-course').addEventListener('click', function () {
        document.querySelector('#already-course').style.display = "none";
        document.querySelector('#new-course').style.display = "none";
        document.querySelector('#tees').value = 'Tees';
        document.querySelector('#course-exists').value = 'Course';
        document.querySelector('#new-course').style.display = "block";
        document.querySelector('#course-or-tees').value = "Course";
        return false;
    })

    // Clear new course option when new tee is selected
    document.querySelector('#new-course-or-tees-tees').addEventListener('click', function () {
        document.querySelector('#already-course').style.display = "none";
        document.querySelector('#new-course').style.display = "none";
        document.querySelector('#new-tees').value = 'Tees';
        document.querySelector('#new-course-name').value = '';
        document.querySelector('#already-course').style.display = "block";
        document.querySelector('#course-or-tees').value = "Tees";
        return false;
    })
})

// Check user input
function validateMyForm() {
    let alreadyCourse = document.querySelector('#already-course');
    let newCourse = document.querySelector('#new-course');
    // Check if the user selected new course or new tees
    if (alreadyCourse.style.display === 'none' && newCourse.style.display === 'none') {
        alert("Please choose if you are adding an entirely new course or just new tees.");
        return false;
    } 
    // Check if user selected entirely new course
    else if (alreadyCourse.style.display === 'none') {
        let tees = document.querySelector('#new-tees');
        let courseName = document.querySelector('#new-course-name');
        // Check if user selected a valid tee option
        if (tees.value === 'Tees') {
            alert("Please select an option for the tees.");
            return false;
        } 
        // Check if user entered a valid course name
        if (courseName.value === '') {
            alert("Please enter a course name.");
            return false;
        } 
    } 
    // Check if user selected a new tee option
    else if (newCourse.style.display === 'none') {
        let tees = document.querySelector('#tees');
        let courseName = document.querySelector('#courseexists');
        // Check if user selected a valid tee option
        if (tees.value === 'Tees') {
            alert("Please select an option for the tees.");
            return false;
        } 
        // Check if user selected a valid course name
        if (courseName.value === 'Course') {
            alert("Please select an option for the course name.");
            return false;
        }
    }

    // Check if all the numbers on the scorecard add up
    let yardageRow = document.getElementsByClassName('yardages-row')[0];
    let parRow = document.getElementsByClassName('pars-row')[0];
    let handicapRow = document.getElementsByClassName('handicap-row')[0];
    let yardages = [];
    let pars = [];
    let handicaps = [];
    // Populate yardages, pars, and handicaps the user entered
    for (let i = 0; i < yardageRow.childElementCount; i++) {
        // Only on the rows of the scorecard that matter
        if (i != 0 && i != 10 && i != 20 && i != 21) {
            yardages.push(yardageRow.children[i].children[0].value);
            pars.push(parRow.children[i].children[0].value);
            handicaps.push(handicapRow.children[i].children[0].value);
        }
    }
    // Check the users math
    let frontNineSumYardages = 0;
    let backNineSumYardages = 0;
    let totalSumYardages = 0;
    let frontNineSumPars = 0;
    let backNineSumPars = 0;
    let totalSumPars = 0;
    for (let i = 0; i < 18; i++) {
        if (i < 9) {
            frontNineSumYardages += parseInt(yardages[i]);
            totalSumYardages += parseInt(yardages[i]);
            frontNineSumPars += parseInt(pars[i]);
            totalSumPars += parseInt(pars[i]);
        }
        else {
            backNineSumYardages += parseInt(yardages[i]);
            totalSumYardages += parseInt(yardages[i]);
            backNineSumPars += parseInt(pars[i]);
            totalSumPars += parseInt(pars[i]);
        }
    }
    let frontNineYardageGiven = yardageRow.children[10].children[0].value;
    let backNineYardageGiven = yardageRow.children[20].children[0].value;
    let totalYardageGiven = yardageRow.children[21].children[0].value;
    let frontNineParGiven = parRow.children[10].children[0].value;
    let backNineParGiven = parRow.children[20].children[0].value;
    let totalParGiven = parRow.children[21].children[0].value;

    // Front nine yardage does not add up
    if (frontNineSumYardages != frontNineYardageGiven) {
        alert("The front nine yardages do not add up to the front nine yardage total.");
        return false;
    } 
    // Back nine yardage does not add up
    else if (backNineSumYardages != backNineYardageGiven) {
        alert("The back nine yardages do not add up to the back nine yardage total.");
        return false;
    } 
    // Total yardage does not add up
    else if (totalSumYardages != totalYardageGiven) {
        alert("The yardages by hole do not add up to the yardage total.");
        return false;
    } 
    // Front nine pars do not add up
    else if (frontNineSumPars != frontNineParGiven) {
        alert("The front nine pars do not add up to the front nine par total.");
        return false;
    } 
    // Back nine pars do not add up
    else if (backNineSumPars != backNineParGiven) {
        alert("The back nine pars do not add up to the back nine par total.");
        return false;
    } 
    // Total pars do not add up
    else if (totalSumPars != totalParGiven) {
        alert("The pars by hole do not add up to the par total.");
        return false;
    } 
    // Check handicap row does not have duplicates
    let handicapSet = new Set(handicaps);
    if (handicapSet.size != handicaps.length) {
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