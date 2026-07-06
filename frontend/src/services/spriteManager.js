/**
 * Vehicle Sprite Manager
 * Load và cache vehicle sprites cho rendering
 * Shared module cho tất cả components
 */

// Sprite paths - có thể mở rộng thêm
const SPRITE_PATHS = {
  car: {
    default: "/sprites/vehicles/sports_car_red.png",
    variants: [
      "/sprites/vehicles/sports_car_red.png",
      "/sprites/vehicles/sports_car_blue.png",
      "/sprites/vehicles/sports_car_yellow.png",
    ],
  },
  truck: {
    default: "/sprites/vehicles/sports_car_red.png",
  },
  bus: {
    default: "/sprites/vehicles/sports_car_red.png",
  },
  motorcycle: {
    default: null, // Will use inline sprite
  },
  person: {
    default: null, // Will use inline sprite
  },
};

// Sprite cache
const spriteCache = new Map();
const spriteImages = {};
let isPreloaded = false;
let inlineSpritesGenerated = false;

// Generate inline sprites (pedestrian, motorcycle silhouettes)
function generateInlineSprites() {
  if (inlineSpritesGenerated) return;
  inlineSpritesGenerated = true;

  // Pedestrian sprite - 64x64 canvas
  const pedCanvas = document.createElement('canvas');
  pedCanvas.width = 64;
  pedCanvas.height = 64;
  const pedCtx = pedCanvas.getContext('2d');

  // Draw pedestrian silhouette
  pedCtx.fillStyle = '#2ecc71';
  // Head
  pedCtx.beginPath();
  pedCtx.arc(32, 10, 8, 0, Math.PI * 2);
  pedCtx.fill();
  // Body
  pedCtx.fillRect(28, 18, 8, 24);
  // Arms
  pedCtx.fillRect(20, 20, 8, 4);
  pedCtx.fillRect(36, 20, 8, 4);
  // Legs
  pedCtx.fillRect(28, 42, 5, 18);
  pedCtx.fillRect(33, 42, 5, 18);

  const pedImg = new Image();
  pedImg.src = pedCanvas.toDataURL();
  spriteImages.person = {
    img: pedImg,
    width: 64,
    height: 64,
    aspectRatio: 1,
  };

  // Motorcycle sprite - 80x48 canvas
  const motoCanvas = document.createElement('canvas');
  motoCanvas.width = 80;
  motoCanvas.height = 48;
  const motoCtx = motoCanvas.getContext('2d');

  // Draw motorcycle
  motoCtx.fillStyle = '#e74c3c';
  // Body
  motoCtx.beginPath();
  motoCtx.ellipse(40, 28, 28, 12, 0, 0, Math.PI * 2);
  motoCtx.fill();
  // Handlebar
  motoCtx.fillRect(55, 18, 6, 12);
  // Seat
  motoCtx.fillRect(25, 20, 20, 8);
  // Wheels
  motoCtx.fillStyle = '#1a1a1a';
  motoCtx.beginPath();
  motoCtx.arc(18, 36, 8, 0, Math.PI * 2);
  motoCtx.fill();
  motoCtx.beginPath();
  motoCtx.arc(62, 36, 8, 0, Math.PI * 2);
  motoCtx.fill();

  const motoImg = new Image();
  motoImg.src = motoCanvas.toDataURL();
  spriteImages.motorcycle = {
    img: motoImg,
    width: 80,
    height: 48,
    aspectRatio: 80 / 48,
  };
}

// Load single sprite
export function loadSprite(src) {
  return new Promise((resolve, reject) => {
    if (spriteCache.has(src)) {
      resolve(spriteCache.get(src));
      return;
    }

    const img = new Image();
    img.onload = () => {
      spriteCache.set(src, img);
      resolve(img);
    };
    img.onerror = () => {
      reject(new Error(`Failed to load sprite: ${src}`));
    };
    img.src = src;
  });
}

// Preload all sprites
export async function preloadSprites() {
  if (isPreloaded) return;
  isPreloaded = true;

  // Generate inline sprites first
  generateInlineSprites();

  const loadPromises = [];

  for (const [vehicleType, config] of Object.entries(SPRITE_PATHS)) {
    if (config.variants) {
      spriteImages[vehicleType] = [];
      config.variants.forEach((src, index) => {
        loadPromises.push(
          loadSprite(src)
            .then((img) => {
              spriteImages[vehicleType][index] = {
                img,
                width: img.width,
                height: img.height,
                aspectRatio: img.width / img.height,
              };
            })
            .catch(() => {
              // Silent fail - will use fallback
            })
        );
      });
    } else {
      loadPromises.push(
        loadSprite(config.default)
          .then((img) => {
            spriteImages[vehicleType] = {
              img,
              width: img.width,
              height: img.height,
              aspectRatio: img.width / img.height,
            };
          })
          .catch(() => {
            // Silent fail - will use fallback
          })
      );
    }
  }

  await Promise.allSettled(loadPromises);
}

// Get sprite cho vehicle type
export function getSprite(vehicleType, variantIndex = 0) {
  const type = vehicleType?.toLowerCase() || "car";
  const sprites = spriteImages[type];

  if (!sprites) {
    return spriteImages.car?.variants?.[0] || spriteImages.car || null;
  }

  if (Array.isArray(sprites)) {
    return sprites[variantIndex % sprites.length] || sprites[0];
  }

  return sprites;
}

// Check if sprites are ready
export function areSpritesReady() {
  return isPreloaded && Object.keys(spriteImages).length > 0;
}

// Get sprite config (size info)
export function getSpriteConfig(vehicleType, bbox) {
  const sprite = getSprite(vehicleType);
  if (!sprite) return null;

  // Calculate sprite size based on bounding box
  const bboxWidth = bbox.x2 - bbox.x1;
  const bboxHeight = bbox.y2 - bbox.y1;

  // Sprite aspect ratio
  const spriteAspect = sprite.aspectRatio;

  // Scale sprite to match bbox width (maintain aspect ratio)
  const scaledWidth = bboxWidth;
  const scaledHeight = bboxWidth / spriteAspect;

  // Center vertically
  const offsetY = (bboxHeight - scaledHeight) / 2;

  return {
    sprite,
    drawX: bbox.x1,
    drawY: bbox.y1 + offsetY,
    drawWidth: scaledWidth,
    drawHeight: scaledHeight,
    originalWidth: sprite.width,
    originalHeight: sprite.height,
  };
}

// Clear cache (for cleanup)
export function clearSpriteCache() {
  spriteCache.clear();
  Object.keys(spriteImages).forEach((key) => delete spriteImages[key]);
  isPreloaded = false;
}

export default {
  loadSprite,
  preloadSprites,
  getSprite,
  getSpriteConfig,
  areSpritesReady,
  clearSpriteCache,
};
