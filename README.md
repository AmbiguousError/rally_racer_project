# Rally Racer - Pygame Project
/dist/RallyRacer.exe grab this exe to run from your Windows machine

## Steal with Pride!
This code is here to be shared, download a copy, create a branch, let others play what you've created! 

## Game Description
Rally Racer is an exciting top-down 2D racing game built with Pygame. Players control a car and compete against AI opponents on procedurally generated tracks featuring defined roads, grass, mud, and various obstacles. The game emphasizes car handling with features like drifting, handbraking, and dynamic interactions with different surfaces and track elements like ramps and hills.

Players can customize their race by selecting the number of laps, car performance (top speed and grip), the number of checkpoints on the course, the number of AI opponents, and the AI's difficulty level, offering a unique experience each race.

**Key Features:**
* Top-down rally racing action with a focus on car handling.
* Procedurally generated courses including:
    * Defined road paths with improved width consistency.
    * Checkpoints, with options for more complex interactions (future: roundabouts).
    * Challenging off-road elements: grass, mud patches, circular hills, and circular ramps.
    * Obstacle placement logic that avoids cluttering the main road.
* Player-controlled car with detailed physics for:
    * Speed, acceleration, and braking.
    * Drifting and handbrake mechanics.
    * Dynamic jumps with visual lift and shadow effects from ramps and hill crests.
    * Varied grip and speed based on surfaces (road, grass, mud).
* AI-controlled opponent cars with customizable difficulty and randomized performance characteristics.
* Customizable race setup: laps, car performance (top speed/grip), number of checkpoints, AI opponents, and AI difficulty.
* Dynamic particle effects for dust (on grass/dirt) and mud splashes.
* Persistent tire tracks left on grass surfaces for added visual immersion.
* In-game HUD displaying speed, RPM, pedal inputs, lap times (relocated for better visibility), and a mini-map.
* Updated pastel color scheme for a more stylish visual presentation.
* Sound effects for engine, skidding, beeps, etc.

## Recent Gameplay Enhancements (As of May 2025)
* **Procedural Roads:** Tracks now feature a generated road path, offering a primary driving surface.
* **Circular Ramps & Hills:** Ramps and hills are now circular, with hills providing a jump when crested.
* **Surface-Dependent Physics:** Driving on grass significantly reduces speed and grip, while mud is even more penalizing. Roads offer the best grip.
* **Persistent Tire Tracks:** Cars leave lasting tire marks on grassy areas.
* **Visual Overhaul:** Implemented a softer, more stylish pastel color palette across the game.
* **UI Improvements:** Lap timer display has been moved to avoid overlap with the minimap.
* **Enhanced Jump Visuals:** Jumps now feature more pronounced visual lift and dynamic shadow scaling for a better sense of height.

## Packages Used

This project primarily relies on the following Python packages:

* **Pygame:** For game development (graphics, sound, input, etc.).
* **NumPy:** For numerical operations, particularly in sound generation.

A `requirements.txt` file is included to facilitate the installation of these dependencies.

## Installation

To set up and run Rally Racer on your local machine, follow these steps:

1.  **Prerequisites:**
    * Ensure you have Python 3.9 or newer installed on your system. You can download it from [python.org](https://www.python.org/).
    * Git is recommended for cloning the project (if applicable) but not strictly necessary if you have the source code directly.

2.  **Clone the Repository (Optional):**
    If you have the project on a Git repository (e.g., GitHub), clone it:
    ```bash
    git clone <repository_url>
    cd rally_racer_project 
    ```
    If you have the files directly, navigate to the project's root directory (`rally_racer_project`).

3.  **Create and Activate a Virtual Environment (Recommended):**
    It's highly recommended to use a virtual environment to manage project dependencies.

    * **Using `venv` (standard Python):**
        ```bash
        # Create the virtual environment (e.g., named 'pyvenv')
        python -m venv pyvenv

        # Activate the virtual environment
        # On Windows:
        # pyvenv\Scripts\activate
        # On macOS/Linux:
        # source pyvenv/bin/activate
        ```

4.  **Install Dependencies:**
    Once your virtual environment is activated, install the required packages using the provided `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```
    This will install Pygame and NumPy and their dependencies.

## How to Run the Game

After successfully installing the dependencies:

1.  Ensure your virtual environment (if you created one) is activated.
2.  Navigate to the root directory of the project (`rally_racer_project`) in your terminal or command prompt.
3.  Run the main game script:
    ```bash
    python main.py
    ```
    (Or `python3 main.py` depending on your system's Python alias).

The game window should appear, starting with the "Race Setup" screen.

## Project Structure

The project is organized into several Python modules for better maintainability:

* `main.py`: The main entry point of the game, containing the game loop and event handling.
* `constants.py`: Stores all global game constants (colors, physics values, UI parameters, etc.).
* `utils.py`: Contains general utility functions (math helpers, collision checks, point-in-polygon).
* `sound_manager.py`: Handles the procedural generation of sound effects.
* `course_generator.py`: Includes functions for procedurally generating track elements like checkpoints, roads, mud, ramps, and visual hills.
* `ui_elements.py`: Contains functions for drawing various UI components (buttons, map, gauges, track background, roads).
* `classes/`: A directory (Python package) containing class definitions for game objects:
    * `__init__.py`: Makes `classes` a package and can expose classes.
    * `car.py`: Defines the `Car` class for player and AI vehicles, including physics and surface interactions.
    * `particle.py`: Defines `Particle` and its derivatives (`DustParticle`, `MudParticle`).
    * `track_elements.py`: Defines classes for `Ramp` (now circular), `MudPatch`, and `Checkpoint`. (Note: `VisualHill` is currently defined in `course_generator.py`).

## Controls

* **Up Arrow / W:** Accelerate
* **Down Arrow / S:** Brake/Reverse
* **Left Arrow / A:** Steer Left
* **Right Arrow / D:** Steer Right
* **Spacebar:** Handbrake

Enjoy the race!