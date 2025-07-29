import { motion } from 'framer-motion';

export default function GradientBackground() {
  return (
    <motion.div
      className="fixed inset-0 -z-10"
      style={{
        background: '#ffffff',
      }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1 }}
    />
  );
}