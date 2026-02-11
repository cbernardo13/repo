const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const axios = require('axios');
const qrcode = require('qrcode-terminal');

const SERVER_URL = 'http://localhost:3000';

yargs(hideBin(process.argv))
    .command('status', 'Check connection status', () => { }, async (argv) => {
        try {
            const res = await axios.get(`${SERVER_URL}/status`);
            console.log('Status:', res.data);
        } catch (e) {
            console.error('Error connecting to server:', e.message);
        }
    })
    .command('login', 'Display QR code for login', () => { }, async (argv) => {
        try {
            const res = await axios.get(`${SERVER_URL}/status`);
            if (res.data.ready) {
                console.log('Already logged in!');
            } else if (res.data.qr) {
                qrcode.generate(res.data.qr, { small: true });
                console.log('Scan the QR code above.');
            } else {
                console.log('Waiting for QR code... (check server logs)');
            }
        } catch (e) {
            console.error('Error:', e.message);
        }
    })
    .command('send', 'Send a message', (yargs) => {
        return yargs
            .option('to', { type: 'string', demandOption: true })
            .option('msg', { type: 'string', demandOption: true });
    }, async (argv) => {
        try {
            const res = await axios.post(`${SERVER_URL}/send`, {
                to: argv.to,
                msg: argv.msg
            });
            console.log('Sent:', res.data);
        } catch (e) {
            console.error('Error sending:', e.response?.data || e.message);
        }
    })
    .command('history', 'Get chat history', (yargs) => {
        return yargs
            .option('to', { type: 'string', demandOption: true })
            .option('limit', { type: 'number', default: 10 });
    }, async (argv) => {
        try {
            const res = await axios.get(`${SERVER_URL}/history`, {
                params: { to: argv.to, limit: argv.limit }
            });
            console.log(JSON.stringify(res.data.history, null, 2));
        } catch (e) {
            console.error('Error fetching history:', e.response?.data || e.message);
        }
    })
    .help()
    .argv;
