document.addEventListener('DOMContentLoaded', function () {

    // Change the tee row to be the same color as the tees
    let tees = document.querySelector('#tees').value;
    let teeRow = document.getElementsByClassName('yardages-row')[0];
    if (tees === 'Blue') {
        teeRow.style.backgroundColor = '#0000ff';
        teeRow.style.color = 'white';
    } else if (tees == 'Black') {
        teeRow.style.backgroundColor = 'black';
        teeRow.style.color = 'white'
    }

    // Create a copy of the golfer scores row to allow for dynamically adding golfers later on
    let originalGolfer = document.getElementsByClassName('scores-row')[0];
    let copyGolfer = originalGolfer.cloneNode(true);

    // Provide the option to switch courses
    document.querySelector('#course').addEventListener('change', function () {
        let course = document.querySelector('#course').value;
        let origin = window.location.origin;
        window.location.replace(`${origin}/post/${course}`);
    })

    // Provide the option to switch tees
    document.querySelector('#tees').addEventListener('change', function () {
        let course = document.querySelector('#course').value;
        let tees = document.querySelector('#tees').value;
        let origin = window.location.origin;
        window.location.replace(`${origin}/post/${course}/${tees}`);
    })

    // Dynamically allocate names for each golfer and score to be passed into request.POST later
    document.querySelector('#golfer').addEventListener('change', function () {
        let golfer = document.querySelector('#golfer').value;
        let allGolfers = document.getElementsByClassName('golfer');
        // Disable the golfer in all other golfer rows
        for (var i = 0; i < allGolfers.length; i++) {
            if (allGolfers[i] != this) {
                for (var j = 0; j < allGolfers.length + 1; j++) {
                    if (allGolfers[i].children[j].value === golfer) {
                        allGolfers[i].children[j].disabled = true;
                    }
                }
            }
        }
        let scores = this.parentElement.parentElement;
        // Allocate names for the golfer and their scores
        for (var i = 0; i < scores.childElementCount; i++) {
            // Allocate name for the golfer
            if (i === 0) {
                let rows = document.querySelector('#golfer').parentElement.parentElement.parentElement.childElementCount;
                let golferCount = rows - 4;
                let thisCard = document.getElementsByClassName('scorecard')[0];
                for (var j = 0; j < golferCount; j++) {
                    if (thisCard.rows[j + 3].children[0].children[0] === this) {
                        scores.children[i].children[0].name = `golfer-${j + 1}`;
                    }
                }
                // Allocate name for the golfers holes
            } else {
                scores.children[i].children[0].name = `${golfer}-${i}`
            }
        }
    })

    // Provide the option to add a golfer
    document.querySelector('#add-golfer').addEventListener('click', function () {
        // Set a limit of a 4 golfer maximum
        let currentGolfers = document.getElementsByClassName('scorecard')[0].children[0].childElementCount - 4;
        if (currentGolfers > 3) {
            alert('4 Golfer Maximum');
            return;
        }
        newGolfer = copyGolfer.cloneNode(true); // Copy a blank golfer template
        let allGolfers = document.getElementsByClassName('golfer');
        // Check which golfers are already selected
        for (var i = 1; i < allGolfers[0].children.length; i++) {
            if (allGolfers[0].children[i].disabled === true || allGolfers[0].children[i].selected === true) {
                newGolfer.children[0].children[0].children[i].disabled = true;
            }
        }
        // Add option to switch golfer
        newGolfer.children[0].children[0].addEventListener('change', function () {
            let golfer = this.value;
            let allGolfers = document.getElementsByClassName('golfer');
            // Disable golfers that are already selected
            for (var i = 0; i < allGolfers.length; i++) {
                if (allGolfers[i] != this) {
                    for (var j = 1; j < allGolfers[0].children.length; j++) {
                        if (allGolfers[i].children[j].value === golfer) {
                            allGolfers[i].children[j].disabled = true;
                        }
                    }
                }
            }
            let scores = this.parentElement.parentElement;
            // Dynamically allocate names for the golfer and their scores to be passed into request.POST later
            for (var i = 0; i < scores.childElementCount; i++) {
                // Allocate golfer name
                if (i === 0) {
                    let rows = document.querySelector('#golfer').parentElement.parentElement.parentElement.childElementCount;
                    let golferCount = rows - 4;
                    let thisCard = document.getElementsByClassName('scorecard')[0];
                    for (var j = 0; j < golferCount; j++) {
                        if (thisCard.rows[j + 3].children[0].children[0] === this) {
                            scores.children[i].children[0].name = `golfer-${j + 1}`;
                        }
                    }
                    // Allocate golfers holes names
                } else {
                    scores.children[i].children[0].name = `${golfer}-${i}`
                }
            }


        })

        // Plop the new row in
        let scorecard = document.querySelector('.scorecard');
        let parRowIndex = document.getElementsByClassName('pars-row')[0].rowIndex;
        var newRow = scorecard.insertRow(parRowIndex);
        newRow.replaceWith(newGolfer);


    })
})

// Validate user data and count golfers
function validate() {
    // Ensure all golfers have been selected
    let scorecard = document.getElementsByClassName('scorecard')[0];
    let rows = scorecard.children[0].rows
    let golferCount = rows.length - 4;
    document.querySelector('#number-of-golfers').value = golferCount;
    for (var i = 0; i < golferCount; i++) {
        if (rows[i + 3].children[0].children[0].value === 'Golfer') {
            alert('Please select a golfer name for each golfer.');
            return false;
        }
    }
    // Ensure all the math adds up for each golfer
    for (let i = 0; i < golferCount; i++) {
        let golferRow = rows[i + 3];
        let golferName = golferRow.children[0].children[0].value;
        let golferScores = [];
        for (let i = 0; i < golferRow.childElementCount; i++) {
            // Only on the rows of the scorecard that matter
            if (i != 0 && i != 10 && i != 20 && i != 21) {
                golferScores.push(golferRow.children[i].children[0].value);
            }
        }
        let frontNineSum = 0;
        let backNineSum = 0;
        let totalSum = 0;
        for (let i = 0; i < 18; i++) {
            if (i < 9) {
                frontNineSum += parseInt(golferScores[i]);
                totalSum += parseInt(golferScores[i]);
            }
            else {
                backNineSum += parseInt(golferScores[i]);
                totalSum += parseInt(golferScores[i]);
            }
        }
        // Check front back and total add up
        if (frontNineSum != parseInt(golferRow.children[10].children[0].value)) {
            alert(`${golferName}'s front nine scores do not add up to the front nine total.`);
            return false;
        }
        else if (backNineSum != parseInt(golferRow.children[20].children[0].value)) {
            alert(`${golferName}'s back nine scores do not add up to the back nine total.`);
            return false;
        }
        else if (totalSum != parseInt(golferRow.children[21].children[0].value)) {
            alert(`${golferName}'s scores do not add up to the total`);
            return false;
        }
    }

}
