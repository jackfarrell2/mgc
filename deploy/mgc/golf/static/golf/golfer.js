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
    let selectGolfer = document.querySelector('#golfer-name');
    for (let i = 0; i < selectGolfer.children.length; i++) {
        if (selectGolfer.children[i].value === golferName) {
            selectGolfer.children[i].selected = true;
        }
    }

    // Change the page when a new golfer is selected
    let golfer = document.querySelector('#golfer-name');
    golfer.addEventListener('change', function () {
        let selectedGolfer = document.querySelector('#golfer-name').value;
        let origin = window.location.origin;
        window.location.replace(`${origin}/golfer/${selectedGolfer}`);
    })

})