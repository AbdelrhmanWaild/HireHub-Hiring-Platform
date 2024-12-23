function filterJobs() {
    const location = document.getElementById('location').value;
    const salary = parseInt(document.getElementById('salary').value) || 0;
    const jobList = document.getElementById('job-list').getElementsByTagName('li');

    for (let i = 0; i < jobList.length; i++) {
        const job = jobList[i];
        const jobLocation = job.getAttribute('data-location');
        const jobSalary = parseInt(job.getAttribute('data-salary'));

        const matchesLocation = location === 'all' || location === jobLocation;
        const matchesSalary = jobSalary >= salary;

        job.style.display = matchesLocation && matchesSalary ? '' : 'none';
    }
}
