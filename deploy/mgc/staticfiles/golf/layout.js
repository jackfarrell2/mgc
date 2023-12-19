document.addEventListener('DOMContentLoaded', function () {
    // Provide the option to switch site version / year
    const year = document.getElementById('year');
    year.addEventListener('change', function () {
        const selected_year = year.value;
        const origin = window.location.origin;
        if (selected_year == '2022') {
            window.location.replace(`${origin}`)
        }
        else {
            window.location.replace(`${origin}/${selected_year}`);
        }
    })
})