document.addEventListener('DOMContentLoaded', function () {

    let tees = document.querySelector('#tees').value;
    let tee_row = document.getElementsByClassName('yardages-row')[0];
    if (tees === 'Blue') {
        tee_row.style.backgroundColor = '#0000ff';
        tee_row.style.color = 'white';
    } else if (tees == 'Black') {
        tee_row.style.backgroundColor = 'black';
        tee_row.style.color = 'white'
    }


    document.querySelector('#course').addEventListener('change', function () {
        let course = document.querySelector('#course').value;
        let origin = window.location.origin;
        window.location.replace(`${origin}/post/${course}`);
    })

    document.querySelector('#tees').addEventListener('change', function () {
        let course = document.querySelector('#course').value;
        let tees = document.querySelector('#tees').value;
        let origin = window.location.origin;
        window.location.replace(`${origin}/post/${course}/${tees}`);
    })

    document.querySelector('#add-golfer').addEventListener('click', function () {
        let original_golfer = document.getElementsByClassName('scores-row')[0];
        let copy_golfer = original_golfer.cloneNode(true);
        var children = copy_golfer.children;
        for (var i = 0; i < children.length; i++) {
            if (i != 0) {
                children[i].value == 0;
            }
        }
        let scorecard = document.querySelector('.scorecard');
        let par_row_index = document.getElementsByClassName('pars-row')[0].rowIndex;
        var new_row = scorecard.insertRow(par_row_index);
        new_row.replaceWith(copy_golfer);

    })
})  