import { Routes, Route } from 'react-router-dom'
import Index from './pages/Index'
import RunGraph from './pages/RunGraph'
import GraphBuilder from './pages/GraphBuilder'
import RunDetail from './pages/RunDetail'
import ProcessedItemDetail from './pages/ProcessedItemDetail'
import Layout from './components/Layout'
import WelcomeScreen from './components/WelcomeScreen'

export default function App() {
  return (
    <>
      <WelcomeScreen />
      <Routes>
        <Route path="/flow/new" element={<GraphBuilder />} />
        <Route path="/flow/:graphId/edit" element={<GraphBuilder />} />
        <Route
          path="/"
          element={
            <Layout>
              <Index />
            </Layout>
          }
        />
        <Route path="/flow/:graphId" element={<RunGraph />} />
        <Route
          path="/runs/:runId"
          element={
            <Layout>
              <RunDetail />
            </Layout>
          }
        />
        <Route
          path="/runs/:runId/items/:itemId"
          element={
            <Layout>
              <ProcessedItemDetail />
            </Layout>
          }
        />
      </Routes>
    </>
  )
}
