const { initializeApp, applicationDefault, cert } = require('firebase-admin/app');
const { getFirestore, Timestamp, FieldValue } = require('firebase-admin/firestore');

const serviceAccount = require('../oatutor-firebase-adminsdk.json');

initializeApp({
  credential: cert(serviceAccount)
});

const db = getFirestore();

const submissionsRef = db.collection('problemSubmissions');
const startRef = db.collection('problemStartLogs');
const userId = "47221";
const pageLen = 2;


// Submissions
var submissions = {}  // key: userId
                      // value: list of submission document objects

async function getSubmissionForUser(userId, endTime) {
    var query;
    if (endTime == 0) {
        query = submissionsRef.where('oats_user_id', '==', userId)
                                    .orderBy('time_stamp', 'desc')
                                    .limit(pageLen);
    } else {
        query = submissionsRef.where('oats_user_id', '==', userId)
                                    .where('time_stamp', '<', endTime)
                                    .orderBy('time_stamp', 'desc')
                                    .limit(pageLen);
    }

    const snapshot = await query.get();
    if (!(userId in submissions)) {
        submissions[userId] = [];
    }
    snapshot.forEach((event) => {
        submissions[userId].push(event.data());
    })

    var lastTime = 0;
    if (snapshot.docs.length > 0) {
        lastTime = snapshot.docs[snapshot.docs.length - 1].data()["time_stamp"];
    }

    return [snapshot.docs.length == pageLen, lastTime];
}

async function* getAllSubmissionsForUser(userId) {
    var lastTime = 0;
    var hasMore = true;
    while (hasMore) {
        const res = await getSubmissionForUser(userId, lastTime);
        hasMore = res[0];
        lastTime = res[1];
        yield hasMore;
    }
    
}

// (async () => {
//     const submissionsGen = getAllSubmissionsForUser(userId);
//     await submissionsGen.next();
//     console.log(submissions);
//     await submissionsGen.next();
//     console.log(submissions);
// })();


// ProblemStartLog
var start = {};

async function getStartForUser(userId, endTime) {
    var query;
    if (endTime == 0) {
        query = startRef.where('oats_user_id', '==', userId)
                        .orderBy('time_stamp', 'desc')
                        .limit(pageLen);
    } else {
        query = startRef.where('oats_user_id', '==', userId)
                        .where('time_stamp', '<', endTime)
                        .orderBy('time_stamp', 'desc')
                        .limit(pageLen);
    }

    const snapshot = await query.get();
    if (!(userId in start)) {
        start[userId] = [];
    }
    snapshot.forEach((event) => {
        start[userId].push(event.data());
    })

    var lastTime = 0;
    if (snapshot.docs.length > 0) {
        lastTime = snapshot.docs[snapshot.docs.length - 1].data()["time_stamp"];
    }

    return [snapshot.docs.length == pageLen, lastTime];
}

async function* getAllStartForUser(userId) {
    var lastTime = 0;
    var hasMore = true;
    while (hasMore) {
        const res = await getStartForUser(userId, lastTime);
        hasMore = res[0];
        lastTime = res[1];
        yield hasMore;
    }
}

(async () => {
    // Submissions
    console.log("===Submission Log===\n")
    const submissionsGen = getAllSubmissionsForUser(userId);
    var submissionIterCount = 0;

    for await (let submissionHasNext of submissionsGen) {
        console.log(submissions);
        console.log("Submission has more to yield:", submissionHasNext);
        submissionIterCount += 1;
        if (submissionIterCount >= 2) {
            break;
        }
    }

    // Start log
    console.log("\n\n===Start Log===\n")

    const startGen = getAllStartForUser(userId);
    var startIterCount = 0;

    for await (let startHasNext of startGen) {
        console.log(start);
        console.log("Start Log has more to yield:", startHasNext);
        startIterCount += 1;
        if (startIterCount >= 2) {
            break;
        }
    }
})();