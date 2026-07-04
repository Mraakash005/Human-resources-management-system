import { type Variants, type Transition } from 'framer-motion';

export const transition: Transition = {
  duration: 0.35,
  ease: 'easeOut',
};

export const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
} as const satisfies Variants;

export const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.35,
      ease: 'easeOut' as const,
    },
  },
} as const satisfies Variants;
