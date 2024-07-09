import { config } from 'dotenv';

config();

console.log('MONGO_DATA_API_ENDPOINT:', process.env.MONGO_DATA_API_ENDPOINT);
console.log('MONGO_DATA_API_KEY:', process.env.MONGO_DATA_API_KEY);
