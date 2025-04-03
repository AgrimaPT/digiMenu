let userInteracted = false;

document.addEventListener('click', function () {
    userInteracted = true;
});

function playOrderSound() {
    const orderSound = new Audio('/static/sounds/order-placed.mp3');
    orderSound.load();

    if (userInteracted) {
        orderSound.play()
            .then(() => console.log("Sound Played"))
            .catch(error => console.error("Error playing sound:", error));
    } else {
        console.warn("User hasn't interacted yet. Sound not played.");
    }
}
