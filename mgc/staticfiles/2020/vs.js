document.addEventListener('DOMContentLoaded', function () {

    // Select the two chosen golfers
    let golferOne = document.getElementsByClassName('strokes')[0].children[0].innerHTML;
    let golferTwo = document.getElementsByClassName('strokes')[1].children[0].innerHTML;

    document.getElementById('golfer-name-one').value = golferOne;
    document.getElementById('golfer-name-two').value = golferTwo;

    // Provide the option to switch golfers
    document.getElementById('vs-submit-button').addEventListener('click', function () {
        let golferOne = document.getElementById('golfer-name-one').value;
        let golferTwo = document.getElementById('golfer-name-two').value;
        let origin = window.location.origin;
        window.location.replace(`${origin}/2020/vs/${golferOne}/${golferTwo}`);
    })

})