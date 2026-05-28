/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        blood: {
          DEFAULT: '#CC0000',
          light: '#FF2222',
          dark: '#880000',
          dim: '#550000',
        },
        terminal: {
          black: '#000000',
          dark: '#0A0A0A',
          panel: '#0D0D0D',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      animation: {
        'flicker': 'flicker 0.15s infinite alternate',
        'scanline': 'scanline 8s linear infinite',
        'glitch-text': 'glitchText 0.3s infinite',
        'pulse-red': 'pulseRed 2s ease-in-out infinite',
        'crt-flicker': 'crtFlicker 0.05s infinite',
        'blood-drip': 'bloodDrip 3s ease-in infinite',
        'shake': 'shake 0.5s cubic-bezier(.36,.07,.19,.97) infinite',
        'earthquake': 'earthquake 0.3s cubic-bezier(.36,.07,.19,.97) infinite',
      },
      keyframes: {
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.85' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        glitchText: {
          '0%, 100%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 1px)' },
          '40%': { transform: 'translate(2px, -1px)' },
          '60%': { transform: 'translate(-1px, -1px)' },
          '80%': { transform: 'translate(1px, 1px)' },
        },
        pulseRed: {
          '0%, 100%': { boxShadow: '0 0 5px #CC0000, inset 0 0 5px #CC0000' },
          '50%': { boxShadow: '0 0 20px #FF0000, inset 0 0 15px #CC0000' },
        },
        crtFlicker: {
          '0%, 100%': { opacity: '0.98' },
          '33%': { opacity: '0.95' },
          '66%': { opacity: '1' },
        },
        bloodDrip: {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '10%': { opacity: '0.7' },
          '90%': { opacity: '0.5' },
          '100%': { transform: 'translateY(100vh)', opacity: '0' },
        },
        shake: {
          '0%, 100%': { transform: 'translate(0)' },
          '10%': { transform: 'translate(-3px, 0)' },
          '20%': { transform: 'translate(3px, 0)' },
          '30%': { transform: 'translate(-2px, 1px)' },
          '40%': { transform: 'translate(2px, -1px)' },
          '50%': { transform: 'translate(-1px, -1px)' },
        },
        earthquake: {
          '0%, 100%': { transform: 'translate(0)' },
          '10%': { transform: 'translate(-8px, 3px)' },
          '20%': { transform: 'translate(7px, -4px)' },
          '30%': { transform: 'translate(-5px, 2px)' },
          '40%': { transform: 'translate(6px, -3px)' },
          '50%': { transform: 'translate(-4px, 5px)' },
          '60%': { transform: 'translate(5px, -2px)' },
          '70%': { transform: 'translate(-3px, 4px)' },
          '80%': { transform: 'translate(4px, -1px)' },
          '90%': { transform: 'translate(-2px, 3px)' },
        },
      },
    },
  },
  plugins: [],
}
