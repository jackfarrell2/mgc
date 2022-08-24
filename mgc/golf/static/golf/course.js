document.addEventListener('DOMContentLoaded', function () {
    
    // Change the yardage row colors according to the course color
    const yardageRows = document.getElementsByClassName('yardages-row')
    for (let i = 0; i < yardageRows.length; i++) {
        if (yardageRows[i].children[0].innerHTML === 'Blue') {
            yardageRows[i].style.backgroundColor = '#0000ff';
            yardageRows[i].style.color = 'white'; 
        } else if (yardageRows[i].children[0].innerHTML === 'Black') {
            yardageRows[i].style.backgroundColor = 'black';
            yardageRows[i].style.color = 'white'; 
        } else if (yardageRows[i].children[0].innerHTML === 'Red') {
            yardageRows[i].style.backgroundColor = 'red';
            yardageRows[i].style.color = 'white'; 
        }
    }

    // Select the chosen golfer
    let golferName = document.getElementsByClassName('handwritten-score')[0].children[0].innerHTML;
    document.querySelector('#golfer-name').value = golferName;
    
    // Allow the user to submit different user and course configurations
    let submitButton = document.querySelector('#submit-button');
    submitButton.addEventListener('click', function () {
        let golfer = document.querySelector('#golfer-name').value;
        let course = document.querySelector('#course-name').value;
        let tee = document.querySelector('#tee-name').value;
        let origin = window.location.origin;
        window.location.replace(`${origin}/courses/${course}/${tee}/${golfer}`);
    })

    // Allow the user to switch between stats, averages, and rounds
    let averages = document.querySelector('#averages');
    let stats = document.querySelector('#course-stats');
    let rounds = document.getElementsByClassName('scorecard-view');
    // Switch to stats
    document.querySelector('#statistics-button').addEventListener('click', function () {
        averages.style.display = 'none';
        for (let i = 0; i < rounds.length; i++) {
            rounds[i].style.display = 'none';
        }
        stats.style.display = 'block';
    })
    // Switch to averages
    document.querySelector('#hole-averages-button').addEventListener('click', function () {
        averages.style.display = 'block';
        for (let i = 0; i < rounds.length; i++) {
            rounds[i].style.display = 'none';
        }
        stats.style.display = 'none';
    })
    //Switch to rounds
    document.querySelector('#rounds-button').addEventListener('click', function () {
        averages.style.display = 'none';
        for (let i = 0; i < rounds.length; i++) {
            rounds[i].style.display = 'block';
        }
        stats.style.display = 'none';
    })

})