class Page404Effects {
  constructor() {
    this.config = {
      particleCount: 15,
      colors: ["#FF6B35", "#FFD23F", "#2C3E50"],
      particleMinSize: 2,
      particleMaxSize: 8,
      particleMinOpacity: 0.2,
      particleMaxOpacity: 0.7,
      particleSpeed: 0.5,
      rippleDuration: 600,
      rippleSize: 20,
    };

    this.selectors = {
      buttons: ".btn",
    };

    this.particles = [];
    this.animationFrameId = null;

    this.init();
  }

  /**
   * Initialize the application
   */
  init() {
    window.addEventListener("load", () => this.setup());
  }

  /**
   * Setup all effects
   */
  setup() {
    this.injectStyles();
    this.createFloatingParticles();
    this.setupButtonEffects();
  }

  /**
   * Inject CSS styles for animations
   */
  injectStyles() {
    const style = document.createElement("style");
    style.textContent = `
      @keyframes ripple {
        to {
          transform: scale(4);
          opacity: 0;
        }
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Generate random number within range
   */
  getRandomInRange(min, max) {
    return Math.random() * (max - min) + min;
  }

  /**
   * Get random color from config
   */
  getRandomColor() {
    const randomIndex = Math.floor(Math.random() * this.config.colors.length);
    return this.config.colors[randomIndex];
  }

  /**
   * Create a single particle element
   */
  createParticle() {
    const particle = document.createElement("div");
    const size = this.getRandomInRange(
      this.config.particleMinSize,
      this.config.particleMaxSize
    );
    const opacity = this.getRandomInRange(
      this.config.particleMinOpacity,
      this.config.particleMaxOpacity
    );

    Object.assign(particle.style, {
      position: "absolute",
      width: `${size}px`,
      height: `${size}px`,
      backgroundColor: this.getRandomColor(),
      borderRadius: "50%",
      opacity: opacity,
      left: `${Math.random() * window.innerWidth}px`,
      top: `${Math.random() * window.innerHeight}px`,
      pointerEvents: "none",
      zIndex: "1",
    });

    return particle;
  }

  /**
   * Create floating particles
   */
  createFloatingParticles() {
    for (let i = 0; i < this.config.particleCount; i++) {
      const element = this.createParticle();
      document.body.appendChild(element);

      this.particles.push({
        element: element,
        x: parseFloat(element.style.left),
        y: parseFloat(element.style.top),
        vx: (Math.random() - 0.5) * this.config.particleSpeed,
        vy: (Math.random() - 0.5) * this.config.particleSpeed,
      });
    }

    this.animateParticles();
  }

  /**
   * Update particle position
   */
  updateParticle(particle) {
    particle.x += particle.vx;
    particle.y += particle.vy;

    // Bounce off edges
    if (particle.x < 0 || particle.x > window.innerWidth) {
      particle.vx *= -1;
    }
    if (particle.y < 0 || particle.y > window.innerHeight) {
      particle.vy *= -1;
    }

    particle.element.style.left = `${particle.x}px`;
    particle.element.style.top = `${particle.y}px`;
  }

  /**
   * Animate all particles
   */
  animateParticles() {
    this.particles.forEach((particle) => this.updateParticle(particle));
    this.animationFrameId = requestAnimationFrame(() =>
      this.animateParticles()
    );
  }

  /**
   * Create ripple effect element
   */
  createRipple(event, button) {
    const ripple = document.createElement("div");
    const x = event.clientX - button.offsetLeft - this.config.rippleSize / 2;
    const y = event.clientY - button.offsetTop - this.config.rippleSize / 2;

    Object.assign(ripple.style, {
      position: "absolute",
      width: `${this.config.rippleSize}px`,
      height: `${this.config.rippleSize}px`,
      background: "rgba(255, 255, 255, 0.6)",
      borderRadius: "50%",
      transform: "scale(0)",
      animation: `ripple ${this.config.rippleDuration}ms linear`,
      left: `${x}px`,
      top: `${y}px`,
    });

    return ripple;
  }

  /**
   * Handle button click with ripple effect
   */
  handleButtonClick(event) {
    const button = event.currentTarget;
    const ripple = this.createRipple(event, button);

    button.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, this.config.rippleDuration);
  }

  /**
   * Setup button effects
   */
  setupButtonEffects() {
    document.querySelectorAll(this.selectors.buttons).forEach((btn) => {
      btn.addEventListener("click", (e) => this.handleButtonClick(e));
    });
  }

  /**
   * Cleanup method to stop animations and remove particles
   */
  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }

    this.particles.forEach((particle) => {
      particle.element.remove();
    });

    this.particles = [];
  }
}

// Initialize the application when DOM is ready
new Page404Effects();
