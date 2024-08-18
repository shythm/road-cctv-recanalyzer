import { streamReadAll } from "./client";

function App() {
  streamReadAll().then((res) => {
    console.log(res);
  });

  return <div>Hello, world!</div>;
}

export default App;
