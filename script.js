document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize EmailJS SDK
    emailjs.init("RQZSVoCyhyiZNoMNt");

    // 2. Mobile Navigation Toggle
    const mobileToggle = document.getElementById('mobileToggle');
    const navLinks = document.getElementById('navLinks');

    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });

        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
            });
        });
    }

    // 3. Hero Video Slider Controls (With Forced Autoplay Fix)
    const slides = document.querySelectorAll('.hero-slide');
    const dots = document.querySelectorAll('.slider-dots .dot');
    let currentSlide = 0;

    function goToSlide(index) {
        slides.forEach(slide => {
            slide.classList.remove('active');
            const video = slide.querySelector('video');
            if (video) {
                video.pause();
            }
        });
        dots.forEach(dot => dot.classList.remove('active'));

        slides[index].classList.add('active');
        dots[index].classList.add('active');
        currentSlide = index;

        // Force active slide video to play
        const activeVideo = slides[index].querySelector('video');
        if (activeVideo) {
            activeVideo.muted = true; // Required for mobile autoplay policy
            activeVideo.currentTime = 0;
            const playPromise = activeVideo.play();
            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    console.log("Autoplay policy error:", error);
                });
            }
        }
    }

    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            const target = parseInt(dot.getAttribute('data-target'));
            goToSlide(target);
        });
    });

    setInterval(() => {
        let nextSlide = (currentSlide + 1) % slides.length;
        goToSlide(nextSlide);
    }, 7000);

    // Initial force-play for Slide 0 on load
    goToSlide(0);

    // 4. Destination Select Dropdown & Categories Init
    const destinationSelect = document.getElementById('destinationSelect');
    const resortCategorySelect = document.getElementById('resortCategorySelect');

    const starCategories = [
        "03 Star",
        "04 Star",
        "05 Star"
    ];

    function updateResortOptions() {
        if (!resortCategorySelect) return;
        resortCategorySelect.innerHTML = '<option value="" disabled selected>Select Category</option>';

        starCategories.forEach(category => {
            const optionEl = document.createElement('option');
            optionEl.value = category;
            optionEl.textContent = category;
            resortCategorySelect.appendChild(optionEl);
        });
    }

    updateResortOptions();

    if (destinationSelect) {
        destinationSelect.addEventListener('change', (e) => {
            if (e.target.value === "Thailand") goToSlide(1);
            else if (e.target.value === "Maldives") goToSlide(0);
        });
    }

    // 5. Flatpickr Range Datepicker with Duration Calc
    const durationInput = document.getElementById('duration');
    const datePickerInput = document.getElementById('datePicker');
    
    if (datePickerInput) {
        flatpickr("#datePicker", {
            mode: "range",
            dateFormat: "Y-m-d",
            minDate: "today",
            onChange: function(selectedDates) {
                if (selectedDates.length === 2) {
                    const checkIn = selectedDates[0];
                    const checkOut = selectedDates[1];
                    const diffTime = Math.abs(checkOut - checkIn);
                    const nights = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    const days = nights + 1;

                    if (durationInput) {
                        durationInput.value = `${nights} Nights / ${days} Days`;
                    }
                } else {
                    if (durationInput) durationInput.value = "";
                }
            }
        });
    }

    // 6. Compact All-in-One Guests Stepper Control
    let adultsCount = 2;
    let kidsCount = 0;

    const adultsVal = document.getElementById('adultsVal');
    const adultsMinus = document.getElementById('adultsMinus');
    const adultsPlus = document.getElementById('adultsPlus');

    const kidsVal = document.getElementById('kidsVal');
    const kidsMinus = document.getElementById('kidsMinus');
    const kidsPlus = document.getElementById('kidsPlus');

    const childAgesInput = document.getElementById('childAgesInput');

    // Adults Stepper Handlers
    if (adultsMinus && adultsPlus && adultsVal) {
        adultsMinus.addEventListener('click', () => {
            if (adultsCount > 1) {
                adultsCount--;
                adultsVal.innerText = adultsCount;
            }
        });

        adultsPlus.addEventListener('click', () => {
            adultsCount++;
            adultsVal.innerText = adultsCount;
        });
    }

    // Kids Stepper & Inline Age Field Toggle
    function toggleChildAgeField() {
        if (!childAgesInput) return;
        if (kidsCount > 0) {
            childAgesInput.classList.remove('hidden');
            childAgesInput.required = true;
        } else {
            childAgesInput.classList.add('hidden');
            childAgesInput.required = false;
            childAgesInput.value = '';
        }
    }

    if (kidsMinus && kidsPlus && kidsVal) {
        kidsMinus.addEventListener('click', () => {
            if (kidsCount > 0) {
                kidsCount--;
                kidsVal.innerText = kidsCount;
                toggleChildAgeField();
            }
        });

        kidsPlus.addEventListener('click', () => {
            kidsCount++;
            kidsVal.innerText = kidsCount;
            toggleChildAgeField();
        });
    }

    // 7. About Modal Functionality
    const aboutModal = document.getElementById('aboutModal');
    const closeAboutModalBtn = document.getElementById('closeAboutModal');
    const aboutTriggers = document.querySelectorAll('.about-trigger');

    aboutTriggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            if (aboutModal) aboutModal.classList.add('active');
        });
    });

    if (closeAboutModalBtn && aboutModal) {
        closeAboutModalBtn.addEventListener('click', () => {
            aboutModal.classList.remove('active');
        });

        window.addEventListener('click', (e) => {
            if (e.target === aboutModal) {
                aboutModal.classList.remove('active');
            }
        });
    }

    // 8. Form Submission via EmailJS & Success Pop-Up Modal
    const inquiryForm = document.getElementById('inquiryForm');
    const successModal = document.getElementById('successModal');
    const closeSuccessModalBtn = document.getElementById('closeSuccessModal');

    if (closeSuccessModalBtn && successModal) {
        closeSuccessModalBtn.addEventListener('click', () => {
            successModal.classList.remove('active');
        });

        window.addEventListener('click', (e) => {
            if (e.target === successModal) {
                successModal.classList.remove('active');
            }
        });
    }

    if (inquiryForm) {
        inquiryForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const submitBtn = inquiryForm.querySelector('.submit-btn');
            const originalBtnText = submitBtn.innerText;
            submitBtn.innerText = "Sending...";
            submitBtn.disabled = true;

            const formData = new FormData(this);
            const selectedDestination = destinationSelect ? destinationSelect.value : 'Maldives';

            const templateParams = {
                name: formData.get('name'),
                email: formData.get('email'),
                phone: formData.get('phone'),
                departure_city: formData.get('departure_city'),
                travel_dates: formData.get('travel_dates'),
                duration: formData.get('duration'),
                adults: `${adultsCount} Adult(s)`,
                children: `${kidsCount} Kid(s)`,
                child_ages: formData.get('child_ages') || 'N/A',
                hotel_category: formData.get('hotel_category'),
                budget_range: formData.get('budget_range'),
                additional_requirements: formData.get('additional_requirements') || 'None',
                message: `
New Travel Booking Inquiry (${selectedDestination}):
-----------------------------
- Destination: ${selectedDestination}
- Customer Name: ${formData.get('name')}
- Email Address: ${formData.get('email')}
- Phone / WhatsApp: ${formData.get('phone')}
- Departure City: ${formData.get('departure_city')}
- Travel Dates: ${formData.get('travel_dates')}
- Duration: ${formData.get('duration')}
- Guests: ${adultsCount} Adult(s), ${kidsCount} Kid(s) (Ages: ${formData.get('child_ages') || 'N/A'})
- Hotel Category: ${formData.get('hotel_category')}
- Budget Range: ${formData.get('budget_range')}
- Additional Requirements: ${formData.get('additional_requirements') || 'None'}
                `.trim()
            };

            emailjs.send('service_w7wk7ea', 'template_f7s6onv', templateParams)
                .then(() => {
                    if (successModal) successModal.classList.add('active');
                    inquiryForm.reset();
                    
                    adultsCount = 2;
                    kidsCount = 0;
                    if (adultsVal) adultsVal.innerText = adultsCount;
                    if (kidsVal) kidsVal.innerText = kidsCount;
                    if (childAgesInput) {
                        childAgesInput.classList.add('hidden');
                        childAgesInput.value = '';
                    }
                    if (durationInput) durationInput.value = "";
                    if (destinationSelect) destinationSelect.selectedIndex = 0;

                    submitBtn.innerText = originalBtnText;
                    submitBtn.disabled = false;
                }, (error) => {
                    alert('Failed to send email. Please try again.');
                    console.error('EmailJS Error:', error);
                    submitBtn.innerText = originalBtnText;
                    submitBtn.disabled = false;
                });
        });
    }
});
