import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Web3 霓虹色彩系统
        primary: {
          DEFAULT: '#06B6D4',      // Cyan-500
          light: '#22D3EE',        // Cyan-400
          dark: '#0891B2',         // Cyan-600
          neon: '#00F5FF',         // Neon cyan
        },
        secondary: {
          DEFAULT: '#8B5CF6',      // Violet-500
          light: '#A78BFA',        // Violet-400
          dark: '#7C3AED',         // Violet-600
          neon: '#A855F7',         // Neon purple
        },
        accent: {
          DEFAULT: '#EC4899',      // Pink-500
          light: '#F472B6',        // Pink-400
          dark: '#DB2777',         // Pink-600
          neon: '#FF00FF',         // Neon magenta
        },
        success: {
          DEFAULT: '#10B981',      // Green-500
          light: '#34D399',        // Green-400
          neon: '#00FF88',         // Neon green
        },
        danger: {
          DEFAULT: '#EF4444',      // Red-500
          light: '#F87171',        // Red-400
          neon: '#FF0055',         // Neon red
        },
        warning: {
          DEFAULT: '#F59E0B',      // Amber-500
          light: '#FBBF24',        // Amber-400
          neon: '#FFD700',         // Neon gold
        },

        // 玻璃态系统 - 升级版
        glass: {
          DEFAULT: 'rgba(15, 23, 42, 0.7)',     // Slate-900 with opacity
          light: 'rgba(30, 41, 59, 0.6)',       // Slate-800 with opacity
          dark: 'rgba(2, 6, 23, 0.8)',          // Almost black
          border: 'rgba(148, 163, 184, 0.1)',   // Slate-400 subtle
          highlight: 'rgba(255, 255, 255, 0.05)', // White highlight
        },

        // 背景系统 - Web3深色
        bg: {
          primary: '#020617',      // Slate-950
          secondary: '#0f172a',    // Slate-900
          tertiary: '#1e293b',     // Slate-800
          card: 'rgba(15, 23, 42, 0.5)',
        },

        // 边框光晕
        glow: {
          cyan: 'rgba(6, 182, 212, 0.5)',
          purple: 'rgba(139, 92, 246, 0.5)',
          pink: 'rgba(236, 72, 153, 0.5)',
          green: 'rgba(16, 185, 129, 0.5)',
        },
      },
      spacing: {
        // 8px baseline spacing system
        '1': '0.25rem',   // 4px
        '2': '0.5rem',    // 8px
        '3': '0.75rem',   // 12px
        '4': '1rem',      // 16px
        '6': '1.5rem',    // 24px
        '8': '2rem',      // 32px
        '10': '2.5rem',   // 40px
        '12': '3rem',     // 48px
      },
      borderRadius: {
        'sm': '0.25rem',  // 4px
        'md': '0.5rem',   // 8px
        'lg': '0.75rem',  // 12px
        'xl': '1rem',     // 16px
        '2xl': '1.5rem',  // 24px
        'full': '9999px',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',

        // Web3 霓虹光晕阴影
        'glow-sm': '0 0 10px rgba(6, 182, 212, 0.3)',
        'glow-md': '0 0 20px rgba(6, 182, 212, 0.4)',
        'glow-lg': '0 0 30px rgba(6, 182, 212, 0.5)',
        'glow-cyan': '0 0 20px rgba(6, 182, 212, 0.6), 0 0 40px rgba(6, 182, 212, 0.3)',
        'glow-purple': '0 0 20px rgba(139, 92, 246, 0.6), 0 0 40px rgba(139, 92, 246, 0.3)',
        'glow-pink': '0 0 20px rgba(236, 72, 153, 0.6), 0 0 40px rgba(236, 72, 153, 0.3)',
        'glow-green': '0 0 20px rgba(16, 185, 129, 0.6), 0 0 40px rgba(16, 185, 129, 0.3)',

        // 内阴影光晕
        'inner-glow': 'inset 0 0 20px rgba(6, 182, 212, 0.1)',
      },
      backdropBlur: {
        'glass': '20px',
        'glass-sm': '12px',
        'glass-lg': '32px',
      },
      backgroundImage: {
        // Web3渐变背景
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-cyber': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-neon': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'gradient-ocean': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'gradient-sunset': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 3s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(6, 182, 212, 0.2), 0 0 10px rgba(6, 182, 212, 0.1)' },
          '100%': { boxShadow: '0 0 20px rgba(6, 182, 212, 0.4), 0 0 30px rgba(6, 182, 212, 0.2)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
}

export default config
