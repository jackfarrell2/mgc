document.addEventListener('DOMContentLoaded', function () {

    // Change the tee row to be the same color as the tees
    let tees = document.querySelector('#tees').value;
    let tee_row = document.getElementsByClassName('yardages-row')[0];
    if (tees === 'Blue') {
        tee_row.style.backgroundColor = '#0000ff';
        tee_row.style.color = 'white';
    } else if (tees == 'Black') {
        tee_row.style.backgroundColor = 'black';
        tee_row.style.color = 'white'
    }

    // Create a copy of the golfer scores row to allow for dynamically adding golfers later on
    let original_golfer = document.getElementsByClassName('scores-row')[0];
    let copy_golfer = original_golfer.cloneNode(true);

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
        let all_golfers = document.getElementsByClassName('golfer');
        // Disable the golfer in all other golfer rows
        for (var i = 0; i < all_golfers.length; i++) {
            if (all_golfers[i] != this) {
                for (var j = 0; j < all_golfers.length + 1; j++) {
                    if (all_golfers[i].children[j].value === golfer) {
                        all_golfers[i].children[j].disabled = true;
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
                let golfer_count = rows - 4;
                let this_card = document.getElementsByClassName('scorecard')[0];
                for (var j = 0; j < golfer_count; j++) {
                    if (this_card.rows[j + 3].children[0].children[0] === this) {
                        scores.children[i].children[0].name = `golfer_${j + 1}`;
                    }
                }
                // Allocate name for the golfers holes
            } else {
                scores.children[i].children[0].name = `${golfer}_${i}`
            }
        }
    })

    // Provide the option to add a golfer
    document.querySelector('#add-golfer').addEventListener('click', function () {
        // Set a limit of a 4 golfer maximum
        let current_golfers = document.getElementsByClassName('scorecard')[0].children[0].childElementCount - 4;
        if (current_golfers > 3) {
            alert('4 Golfer Maximum');
            return;
        }
        new_golfer = copy_golfer.cloneNode(true); // Copy a blank golfer template
        let all_golfers = document.getElementsByClassName('golfer');
        // Check which golfers are already selected
        for (var i = 1; i < all_golfers[0].children.length; i++) {
            if (all_golfers[0].children[i].disabled === true || all_golfers[0].children[i].selected === true) {
                new_golfer.children[0].children[0].children[i].disabled = true;
            }
        }
        // Add option to switch golfer
        new_golfer.children[0].children[0].addEventListener('change', function () {
            let golfer = this.value;
            let all_golfers = document.getElementsByClassName('golfer');
            // Disable golfers that are already selected
            for (var i = 0; i < all_golfers.length; i++) {
                if (all_golfers[i] != this) {
                    for (var j = 1; j < all_golfers[0].children.length; j++) {
                        if (all_golfers[i].children[j].value === golfer) {
                            all_golfers[i].children[j].disabled = true;
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
                    let golfer_count = rows - 4;
                    let this_card = document.getElementsByClassName('scorecard')[0];
                    for (var j = 0; j < golfer_count; j++) {
                        if (this_card.rows[j + 3].children[0].children[0] === this) {
                            scores.children[i].children[0].name = `golfer_${j + 1}`;
                        }
                    }
                    // Allocate golfers holes names
                } else {
                    scores.children[i].children[0].name = `${golfer}_${i}`
                }
            }


        })

        // Plop the new row in
        let scorecard = document.querySelector('.scorecard');
        let par_row_index = document.getElementsByClassName('pars-row')[0].rowIndex;
        var new_row = scorecard.insertRow(par_row_index);
        new_row.replaceWith(new_golfer);


    })

})

// Ensure all golfers have been selected
function validate() {
    let scorecard = document.getElementsByClassName('scorecard')[0];
    let rows = scorecard.children[0].rows
    let golfer_count = rows.length - 4;
    for (var i = 0; i < golfer_count; i++) {
        if (rows[i + 3].children[0].children[0].value === 'Golfer') {
            alert('Please select a golfer name for each golfer.');
            return false;
        }
    }

    return true;
}
