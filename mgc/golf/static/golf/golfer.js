document.addEventListener('DOMContentLoaded', function () {
    
    // Change the yardage row colors according to the course color
    const yardage_rows = document.getElementsByClassName('yardages-row')
    for (let i = 0; i < yardage_rows.length; i++) {
        if (yardage_rows[i].children[0].innerHTML === 'Blue') {
            yardage_rows[i].style.backgroundColor = '#0000ff';
            yardage_rows[i].style.color = 'white'; 
        } else if (yardage_rows[i].children[0].innerHTML === 'Black') {
            yardage_rows[i].style.backgroundColor = 'black';
            yardage_rows[i].style.color = 'white'; 
        } else if (yardage_rows[i].children[0].innerHTML === 'Red') {
            yardage_rows[i].style.backgroundColor = 'red';
            yardage_rows[i].style.color = 'white'; 
        }
    }

    // Select the chosen golfer
    let golfer_name = document.getElementsByClassName('handwritten-score')[0].children[0].innerHTML;
    let select_golfer = document.querySelector('#golfer-name');
    for (let i = 0; i < select_golfer.children.length; i++) {
        if (select_golfer.children[i].value === golfer_name) {
            select_golfer.children[i].selected = true;
        }
    }

    // Change the page when a new golfer is selected
    let golfer = document.querySelector('#golfer-name');
    golfer.addEventListener('change', function () {
        let selected_golfer = document.querySelector('#golfer-name').value;
        let origin = window.location.origin;
        window.location.replace(`${origin}/golfer/${selected_golfer}`);
    })

})