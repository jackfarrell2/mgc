// Validate user data
function validate() {
    // Ensure all golfers have been selected
    let scorecard = document.getElementsByClassName('scorecard')[0];
    let rows = scorecard.children[0].rows
    let golferCount = rows.length - 4;
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
