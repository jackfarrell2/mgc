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
    let original_golfer = document.getElementsByClassName('scores-row')[0];
    let copy_golfer = original_golfer.cloneNode(true);

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

    document.querySelector('#golfer').addEventListener('change', function() {
        let golfer = document.querySelector('#golfer').value;
        let all_golfers = document.getElementsByClassName('golfer');
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
        for (var i = 0; i < scores.childElementCount; i++) {
            if (i === 0) {
                let rows = document.querySelector('#golfer').parentElement.parentElement.parentElement.childElementCount;
                let golfer_count = rows - 4;
                let this_card = document.getElementsByClassName('scorecard')[0];
                for (var j = 0; j < golfer_count; j++) {
                    if (this_card.rows[j + 3].children[0].children[0] === this) {
                        scores.children[i].children[0].name = `golfer_${j + 1}`;
                    }
                }
            } else {
                scores.children[i].children[0].name = `${golfer}_${i}`
            }
        }
    })

    document.querySelector('#add-golfer').addEventListener('click', function () {
        let current_golfers = document.getElementsByClassName('scorecard')[0].children[0].childElementCount - 4;
        if (current_golfers > 3) {
            alert('4 Golfer Maximum');
            return;
        }
        new_golfer = copy_golfer.cloneNode(true);
        let all_golfers = document.getElementsByClassName('golfer');
        for (var i = 1; i < all_golfers[0].children.length; i++) {
            if (all_golfers[0].children[i].disabled === true || all_golfers[0].children[i].selected === true) {
                new_golfer.children[0].children[0].children[i].disabled = true;
            }
        }
        new_golfer.children[0].children[0].addEventListener('change', function() {
            let golfer = this.value;
            let all_golfers = document.getElementsByClassName('golfer');
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
        for (var i = 0; i < scores.childElementCount; i++) {
            if (i === 0) {
                let rows = document.querySelector('#golfer').parentElement.parentElement.parentElement.childElementCount;
                let golfer_count = rows - 4;
                let this_card = document.getElementsByClassName('scorecard')[0];
                for (var j = 0; j < golfer_count; j++) {
                    if (this_card.rows[j + 3].children[0].children[0] === this) {
                        scores.children[i].children[0].name = `golfer_${j + 1}`;
                    }
                }
            } else {
                scores.children[i].children[0].name = `${golfer}_${i}`
            }
        }
        

        })
        
        let scorecard = document.querySelector('.scorecard');
        let par_row_index = document.getElementsByClassName('pars-row')[0].rowIndex;
        var new_row = scorecard.insertRow(par_row_index);
        new_row.replaceWith(new_golfer);


    })
})  